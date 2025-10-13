# Mkdocs-Matplotlib

**Mkdocs-Matplotlib** is a plugin for [mkdocs](https://www.mkdocs.org/) which allows you to automatically generate matplotlib figures and add them to your documentation.
Simply write the code as markdown into your documention.

## Quick Start

This plugin can be installed with `pip`

```shell
pip install mkdocs-matplotlib
```
To enable this plugin for mkdocs you need to add the following lines to your `mkdocs.yml`.

```yaml
plugins:
  - mkdocs_matplotlib
```

To render a code cell using matplotlib you simply have to add the comment `# mkdocs: render` at the top of the cell.

```python
# mkdocs: render
import matplotlib.pyplot as plt
import numpy as np

xpoints = np.array([1, 8])
ypoints = np.array([3, 10])

plt.plot(xpoints, ypoints)
```

The special comment directives (`# mkdocs: render`, `# mkdocs: hidecode`, `# mkdocs: hideoutput`) are automatically hidden from the rendered code output.

In addition you can add `# mkdocs: hidecode` to hide the code and `# mkdocs: hideoutput` to hide the output image of the cell.

```python
# mkdocs: render
# mkdocs: hidecode
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6])
```

The above code block will only show the rendered figure, not the code.
