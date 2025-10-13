import base64
import re
import tempfile
from textwrap import dedent
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from mkdocs.config.base import Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

RENDER_SWITCH = "# mkdocs: render"
HIDECODE_SWITCH = "# mkdocs: hidecode"
HIDEOUTPUT_SWITCH = "# mkdocs: hideoutput"


def _rendered_image_to_dir(
    save_img_dir: str,
    render_code: str,
    global_namespace: Optional[Dict[str, Any]] = None,
    local_namespace: Optional[Dict[str, Any]] = None,
) -> bool:
    # snippet to save a figure
    clearplot_code = """
    import matplotlib
    matplotlib.use('Agg')  # Set backend within execution context
    import matplotlib.pyplot as plt
    plt.rcdefaults()  # Reset to matplotlib defaults before each execution
    """
    clearplot_code = dedent(clearplot_code)

    savefig_code = f"""
    plt.savefig("{save_img_dir}", format='png', dpi=100, bbox_inches='tight')
    """
    savefig_code = dedent(savefig_code)
    closefig_code = "plt.close()"
    # create namespace if not passed
    global_namespace = {} if global_namespace is None else global_namespace
    local_namespace = {} if local_namespace is None else local_namespace

    # render image to
    exec(clearplot_code, global_namespace, local_namespace)
    exec(render_code, global_namespace, local_namespace)

    is_empty: bool = eval(
        "not bool(plt.gcf().get_axes())", global_namespace, local_namespace
    )

    if not is_empty:
        exec(savefig_code, global_namespace, local_namespace)

    exec(closefig_code, global_namespace, local_namespace)

    return is_empty


class RenderPlugin(BasePlugin):
    """An `mkdocs` plugin.
    This plugin defines the following event hooks:
    - `on_page_content`
    Check the [Developing Plugins](https://www.mkdocs.org/user-guide/plugins/#developing-plugins) page of `mkdocs`
    for more information about its plugin system.
    """

    def on_page_content(
        self, html: str, page: Page, config: Config, files: Files
    ) -> str:
        """Renders the code cells with matplotlib.

        Search for code cells in the passed HTML string. If there is a code cell and it starts
        with the correct comment, execute it and paste the rendered image in an img tag.
        The special mkdocs comments are stripped from the displayed code.

        Args:
            html: Input Html
            page: Page Info
            config: Mkdocs Config
            files: File Info

        Returns:
            Html with rendered images added.
        """
        soup = BeautifulSoup(html, features="html.parser")

        tags_to_strip = []
        for code_tag in soup.find_all("code"):
            raw_code: str = code_tag.text
            code_lines = raw_code.splitlines()
            is_render = RENDER_SWITCH in code_lines
            is_hidecode = HIDECODE_SWITCH in code_lines
            is_hideoutput = HIDEOUTPUT_SWITCH in code_lines

            # skip if not a multi line code cell
            if code_tag.parent.name != "pre":
                continue

            # only render if cell start with correct comment
            if is_render:
                temp_file = tempfile.NamedTemporaryFile(suffix=".png").name

                # Use fresh namespaces for each code block to prevent style bleeding
                fresh_global_namespace: Dict[str, Any] = {}
                fresh_local_namespace: Dict[str, Any] = {}
                is_empty = _rendered_image_to_dir(
                    temp_file, raw_code, fresh_global_namespace, fresh_local_namespace
                )

                # get parent tag
                parent_code_tag = code_tag.parent

                # insert image tag
                if not is_hideoutput and not is_empty:
                    with open(temp_file, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("ascii")
                        img_tag = soup.new_tag(
                            "img",
                            src="data:image/png;base64," + str(encoded),
                        )
                        parent_code_tag.insert_after(img_tag)
                        img_tag.wrap(soup.new_tag("center"))

                if is_hidecode:
                    parent_code_tag.decompose()
                else:
                    tags_to_strip.append(code_tag)
                    print(f"Added code_tag to strip, raw_code: {repr(raw_code[:100])}")

        # Strip switches from code blocks that were rendered
        for code_tag in tags_to_strip:
            import re
            for span in code_tag.find_all('span', class_=re.compile(r'^c')):
                if span.get_text().strip() in [RENDER_SWITCH, HIDECODE_SWITCH, HIDEOUTPUT_SWITCH]:
                    span.decompose()
            # Remove empty first line span (from switch removal)
            first_span = code_tag.find('span', id=re.compile(r'__span.*-1$'))
            if first_span and first_span.get_text().strip() == '' and all(c.name == 'a' or (isinstance(c, str) and not c.strip()) for c in first_span.contents):
                first_span.extract()

        # Convert back to HTML string
        result_html = str(soup)

        return result_html
