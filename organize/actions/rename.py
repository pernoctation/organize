import os
import logging

from organize.utils import Path, fullpath, find_unused_filename

from .action import Action
from .trash import Trash


class Rename(Action):

    """
    Renames a file.

    :param str name:
        The new filename.
        Can be a format string which uses file attributes from a filter.

    :param bool overwrite:
        specifies whether existing files should be overwritten.
        Otherwise it will start enumerating files (append a counter to the
        filename) to resolve naming conflicts. [Default: False]

    :param str counter_separator:
        specifies the separator between filename and the appended counter.
        Only relevant if **overwrite** is disabled. [Default: ``\' \'``]

    Examples:
        - Convert all .PDF file extensions to lowercase (.pdf):

          .. code-block:: yaml
            :caption: config.yaml

            rules:
              - folders: '~/Desktop'
                filters:
                  - Extension: PDF
                actions:
                  - Rename: "{path.stem}.pdf"

        - Convert **all** file extensions to lowercase:

          .. code-block:: yaml
            :caption: config.yaml

            rules:
              - folders: '~/Desktop'
                filters:
                  - Extension
                actions:
                  - Rename: "{path.stem}.{extension.lower}"
    """

    def __init__(self, name: str, overwrite=False, counter_separator=' '):
        if os.path.sep in name:
            ValueError('Rename only takes a filename as argument. To move '
                       'files between folders use the Move action.')
        self.name = name
        self.overwrite = overwrite
        self.counter_separator = counter_separator
        self.log = logging.getLogger(__name__)

    def run(self, attrs: dict, simulate: bool) -> Path:
        path = attrs['path']
        expanded_name = self.fill_template_tags(self.name, attrs)
        new_path = path.parent / expanded_name

        # handle filename collisions
        new_path_exists = new_path.exists()
        new_path_samefile = new_path_exists and new_path.samefile(path)
        if new_path_exists and not new_path_samefile:
            if self.overwrite:
                self.print('File already exists')
                Trash().run({'path': new_path}, simulate=simulate)
            else:
                new_path = find_unused_filename(
                    path=new_path, separator=self.counter_separator)

        # do nothing if the new name is equal to the old name and the file is
        # the same
        if new_path_samefile and new_path == path:
            self.print('Keep name')
        else:
            self.print('New name: "%s"' % new_path.name)
            if not simulate:
                self.log.info('Renaming "%s" to "%s".', path, new_path)
                path.rename(new_path)
        return new_path

    def __str__(self):
        return 'Rename(name=%s, overwrite=%s, sep=%s)' % (
            self.name, self.overwrite, self.counter_separator)
