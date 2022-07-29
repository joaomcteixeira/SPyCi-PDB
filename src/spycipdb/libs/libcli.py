"""
Operations shared by client interfaces.

Inspired fromIDPConformerGenerator:
https://github.com/julie-forman-kay-lab/IDPConformerGenerator/blob/3aef6b085ec09eeebc5812639a5eb6832c0215cd/src/idpconfgen/libs/libcli.py
"""
import argparse
import sys
from os import cpu_count

from spycipdb import __version__
from spycipdb.libs.libparse import values_to_dict

detailed = "detailed instructions:\n\n{}"


def load_args(ap):
    """Load argparse commands."""
    return ap.parse_args()
    

def maincli(ap, main):
    """CLI entry point."""
    cmd = load_args(ap)
    main(**vars(cmd))


class FolderOrTar(argparse.Action):
    """Checks if input is a folder, files, or tarball."""


    def __call__(self, parser, namespace, values, option_string=None):
        """Checks the extension of input."""
        if values[0].endswith('.tar'):
            setattr(namespace, self.dest, values[0])
        else:
            setattr(namespace, self.dest, values)


class ArgsToTuple(argparse.Action):
    """Convert list of arguments in tuple."""


    def __call__(self, parser, namespace, values, option_string=None):
        """Call the function."""
        setattr(namespace, self.dest, tuple(values))


class ParamsToDict(argparse.Action):
    """
    Convert command-line parameters in an argument to a dictionary.

    Adapted from https://github.com/joaomcteixeira/taurenmd

    Example
    -------
    Where ``-x`` is an optional argument of the command-line client
    interface.
        >>> par1=1 par2='my name' par3=[1,2,3]
        >>> {'par1': 1, 'par2': 'my name', 'par3': [1, 2, 3]}
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """Execute."""
        param_dict = values_to_dict(values)

        namespace.plotvars = param_dict
        setattr(namespace, self.dest, True)


class CustomParser(argparse.ArgumentParser):
    """Custom parser class."""
    
    
    def error(self, message):
        """Present error message."""
        self.print_help()
        sys.stderr.write(f'\nerror: {message}\n')
        sys.exit(2)


def parse_doc_params(docstring):
    """
    Parse client docstrings.

    Separates PROG, DESCRIPTION and USAGE from client main docstring.

    Parameters
    ----------
    docstring : str
        The module docstring.

    Returns
    -------
    tuple
        (prog, description, usage)
    """
    doclines = docstring.lstrip().split('\n')
    prog = doclines[0]
    description = '\n'.join(doclines[2:doclines.index('USAGE:')])
    usage = '\n' + '\n'.join(doclines[doclines.index('USAGE:') + 1:])

    return prog, description, usage


def add_subparser(parser, module):
    """
    Add a subcommand to a parser.

    Parameters
    ----------
    parser : `argparse.add_suparsers object <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers>`_
        The parser to add the subcommand to.

    module
        A python module containing the characteristics of a taurenmd
        client interface. Client interface modules require the following
        attributes: ``__doc__`` which feeds the `description argument <https://docs.python.org/3/library/argparse.html#description>`_
        of `add_parser <https://docs.python.org/3/library/argparse.html#other-utilities>`_,
        ``_help`` which feeds `help <https://docs.python.org/3/library/argparse.html#help>`_,
        ``ap`` which is an `ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_,
        and a ``main`` function, which executes the main logic of the interface.
    """  # noqa: E501
    new_ap = parser.add_parser(
        module._name,
        usage=module._usage,
        # prog=module._prog,
        description=module._prog + '\n\n' + module.ap.description,
        help=module._help,
        parents=[module.ap],
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    new_ap.set_defaults(func=module.main)


def add_version(parser):
    """
    Add version ``-v`` option to parser.

    Displays a message informing the current version.
    Also accessible via ``--version``.

    Parameters
    ----------
    parser : `argparse.ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_
        The argument parser to add the version argument.
    """  # noqa: E501
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        # the _BANNER contains information on the version number
        version=__version__,
        )


def add_argument_pdb_files(parser):
    """
    Add PDBs Files entry to argument parser.

    Parameters
    ----------
    parser : `argparse.ArgumentParser` object
    """
    parser.add_argument(
        'pdb_files',
        help=(
            'Paths to PDB files in the disk. '
            'Accepts a TAR file.'
            ),
        nargs='+',
        action=FolderOrTar,
        )


def add_argument_ncores(parser):
    """Add argument for number of cores to use."""
    ncpus = max(cpu_count() - 1, 1)
    parser.add_argument(
        '-n',
        '--ncores',
        help=(
            'Number of cores to use. If `-n` uses all available '
            'cores except one. To select the exact number of cores '
            'use -n #, where # is the desired number.'
            ),
        type=int,
        default=1,
        const=ncpus,
        nargs='?',
        )


def add_argument_output(parser):
    """Add argument for general output string."""
    parser.add_argument(
        '-o',
        '--output',
        help=(
            'Output file. Defaults to `None`. '
            'Read CLI instructions for `None` behaviour.'
            ),
        type=str,
        default=None,
        )
