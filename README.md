# Mkdocs-Matplotlib

[![PyPI version](https://badge.fury.io/py/mkdocs-matplotlib.svg)](https://badge.fury.io/py/mkdocs-matplotlib)
[![Test](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/test.yml/badge.svg)](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/test.yml)
[![Release Pipeline](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/release.yml/badge.svg)](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/release.yml)
[![Code Quality](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/conde_quality.yml/badge.svg)](https://github.com/AnHo4ng/mkdocs-matplotlib/actions/workflows/conde_quality.yml)
[![Documentation Status](https://readthedocs.org/projects/mkdocs-matplotlib/badge/?version=latest)](https://mkdocs-matplotlib.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/badge/python-3.8-blue.svg)](https://pypi.org/project/kedro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AnHo4ng/mkdocs-matplotlib/blob/master/LICENCE)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)

**Mkdocs-Matplotlib** is a plugin for [mkdocs](https://www.mkdocs.org/) which allows you to automatically generate matplotlib figures and add them to your documentation.
Simply write the code as markdown into your documention.

![screenshot](docs/assets/screenshot.png)

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

You can add the comment `# mkdocs: hidecode` to hide the code and `# mkdocs: hideoutput` to hide the output image of the cell. The special comment directives appear as regular Python comments in the rendered code blocks.

## Configuration

You can customize the plugin behavior by adding configuration options to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_matplotlib:
      align: center       # Options: left, center, right (default: center)
      image_width: 100%   # Default width for rendered images (default: 100%)
      dpi: 150            # Resolution of rendered images (default: 150)
      image_dir: _images/mpl  # Site-relative directory for rendered images (default: _images/mpl)
```

Rendered figures are written into the built site as separate PNG files named
by content hash (e.g. `_images/mpl/8ef646d9fdfede5a.png`) and referenced with
relative `<img>` links, rather than being embedded into the page as base64
data URIs. Identical figures are stored once, pages stay small, and rebuilds
produce byte-identical files for unchanged figures — which keeps diffs and
git-based deployments (e.g. `mike`/`gh-pages`) from ballooning.

### Image Alignment

Control the horizontal alignment of rendered plots:

- **Global configuration**: Set the default alignment for all plots in `mkdocs.yml`
- **Per-plot override**: Use `# mkdocs: align=left`, `# mkdocs: align=center`, or `# mkdocs: align=right` in individual code blocks

Example with left alignment:

```python
# mkdocs: render
# mkdocs: align=left
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [1, 4, 9])
plt.title('Left-aligned plot')
```

### Image Width

Control the size of rendered plots:

- **Global configuration**: Set the default width for all plots in `mkdocs.yml` (can be a percentage like `50%` or a fixed value like `400px`)
- **Per-plot override**: Use `# mkdocs: width=<value>` in individual code blocks

Example with 50% width:

```python
# mkdocs: render
# mkdocs: width=50%
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [1, 4, 9])
plt.title('Half-width plot')
```

All images include `max-width: 100%` and `height: auto` to ensure they remain responsive and maintain their aspect ratio.
