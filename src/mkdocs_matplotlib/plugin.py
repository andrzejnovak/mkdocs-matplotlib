import hashlib
import os
import posixpath
import re
import tempfile
from textwrap import dedent
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup
from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

RENDER_SWITCH = "# mkdocs: render"
HIDECODE_SWITCH = "# mkdocs: hidecode"
HIDEOUTPUT_SWITCH = "# mkdocs: hideoutput"
ALIGN_PATTERN = re.compile(r'# mkdocs: align=(left|center|right)', re.IGNORECASE)
WIDTH_PATTERN = re.compile(r'# mkdocs: width=(.+)', re.IGNORECASE)
HIDE_LINE_PATTERN = re.compile(r'# (markdown-exec|mkdocs): hide')


def _rendered_image_to_dir(
    save_img_dir: str,
    render_code: str,
    global_namespace: Optional[Dict[str, Any]] = None,
    local_namespace: Optional[Dict[str, Any]] = None,
    dpi: int = 150,
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
    plt.savefig(__mkdocs_mpl_savepath__, format='png', dpi={dpi}, bbox_inches='tight', pad_inches=0.2)
    """
    savefig_code = dedent(savefig_code)
    closefig_code = "plt.close()"
    # create namespace if not passed
    global_namespace = {} if global_namespace is None else global_namespace
    local_namespace = {} if local_namespace is None else local_namespace
    # pass the save path via the namespace so arbitrary paths (spaces,
    # Windows separators) survive the exec'd snippet
    local_namespace["__mkdocs_mpl_savepath__"] = save_img_dir

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

    config_scheme = (
        ('align', config_options.Choice(['left', 'center', 'right'], default='center')),
        ('image_width', config_options.Type(str, default='100%')),
        ('dpi', config_options.Type(int, default=150)),
        ('image_dir', config_options.Type(str, default='_images/mpl')),
    )

    def _write_site_image(self, data: bytes, config: Config) -> str:
        """Store image bytes under site_dir and return its site-root-relative path.

        The filename is a content hash, so an identical figure is written (and
        later committed to gh-pages) exactly once, no matter how many pages or
        deploys produce it.
        """
        digest = hashlib.sha256(data).hexdigest()[:16]
        rel_path = posixpath.join(self.config['image_dir'], f"{digest}.png")
        dest = os.path.join(config['site_dir'], *rel_path.split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            with open(dest, "wb") as f:
                f.write(data)
        return rel_path

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

        tags_to_clean = []
        for code_tag in soup.find_all("code"):
            raw_code: str = code_tag.text
            code_lines = raw_code.splitlines()
            is_render = RENDER_SWITCH in code_lines
            is_hidecode = HIDECODE_SWITCH in code_lines
            is_hideoutput = HIDEOUTPUT_SWITCH in code_lines

            # Check for alignment directive
            align_match = None
            for line in code_lines:
                align_match = ALIGN_PATTERN.search(line)
                if align_match:
                    break

            # Check for width directive
            width_match = None
            for line in code_lines:
                width_match = WIDTH_PATTERN.search(line)
                if width_match:
                    break

            # Use per-block alignment if specified, otherwise use plugin default
            alignment = align_match.group(1).lower() if align_match else self.config['align']
            # Use per-block width if specified, otherwise use plugin default
            image_width = width_match.group(1).strip() if width_match else self.config['image_width']

            # skip if not a multi line code cell
            if code_tag.parent.name != "pre":
                continue

            # only render if cell start with correct comment
            if is_render:
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_file = os.path.join(tmpdir, "figure.png")

                    # Use fresh namespaces for each code block to prevent style bleeding
                    fresh_global_namespace: Dict[str, Any] = {}
                    fresh_local_namespace: Dict[str, Any] = {}
                    is_empty = _rendered_image_to_dir(
                        temp_file,
                        raw_code,
                        fresh_global_namespace,
                        fresh_local_namespace,
                        dpi=self.config['dpi'],
                    )

                    # get parent tag
                    parent_code_tag = code_tag.parent

                    # insert image tag
                    if not is_hideoutput and not is_empty:
                        with open(temp_file, "rb") as f:
                            data = f.read()
                        rel_path = self._write_site_image(data, config)
                        # link relative to the page so the site works from any
                        # mount point (e.g. project pages, mike version dirs)
                        src = posixpath.relpath(
                            rel_path, posixpath.dirname(page.url)
                        )
                        img_tag = soup.new_tag(
                            "img",
                            src=src,
                            style=f"width: {image_width}; max-width: 100%; height: auto;"
                        )
                        parent_code_tag.insert_after(img_tag)

                        # Apply alignment based on configuration
                        if alignment == 'center':
                            img_tag.wrap(soup.new_tag("center"))
                        elif alignment == 'left':
                            wrapper = soup.new_tag("div", style="text-align: left;")
                            img_tag.wrap(wrapper)
                        elif alignment == 'right':
                            wrapper = soup.new_tag("div", style="text-align: right;")
                            img_tag.wrap(wrapper)

                if is_hidecode:
                    parent_code_tag.decompose()
                else:
                    # Mark this code block for directive removal
                    tags_to_clean.append((code_tag, raw_code))

        # Remove directive comments from code blocks by working with the HTML structure
        for code_tag, original_code in tags_to_clean:
            # Count leading directive lines
            original_lines = original_code.splitlines()
            directives_count = 0

            for line in original_lines:
                line_stripped = line.strip()
                if (line_stripped in [RENDER_SWITCH, HIDECODE_SWITCH, HIDEOUTPUT_SWITCH] or
                    ALIGN_PATTERN.match(line_stripped) or
                    WIDTH_PATTERN.match(line_stripped)):
                    directives_count += 1
                elif line_stripped == '':
                    pass
                else:
                    break

            if directives_count > 0:
                # Get the HTML content as a string and split by newlines
                html_content = str(code_tag)
                # Remove the <code...> and </code> tags temporarily
                if html_content.startswith('<code'):
                    start_idx = html_content.find('>') + 1
                    end_idx = html_content.rfind('</code>')
                    inner_html = html_content[start_idx:end_idx]

                    # Split into lines (preserving HTML tags)
                    lines = inner_html.split('\n')

                    # Filter out directive and hidden lines
                    cleaned_lines = []
                    for line in lines:
                        line_stripped = line.strip()
                        if (RENDER_SWITCH in line_stripped or
                            HIDECODE_SWITCH in line_stripped or
                            HIDEOUTPUT_SWITCH in line_stripped or
                            ALIGN_PATTERN.search(line_stripped) or
                            WIDTH_PATTERN.search(line_stripped) or
                            HIDE_LINE_PATTERN.search(line)):
                            continue  # skip this line
                        cleaned_lines.append(line)

                    # Remove leading empty lines
                    while cleaned_lines and not cleaned_lines[0].strip():
                        cleaned_lines.pop(0)

                    # Reconstruct the code tag with cleaned content
                    new_inner_html = '\n'.join(cleaned_lines)
                    code_tag.clear()
                    from bs4 import BeautifulSoup as BS
                    code_tag.append(BS(new_inner_html, 'html.parser'))

        # Convert back to HTML string
        result_html = str(soup)

        return result_html
