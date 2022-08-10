"""
Back-calculates the NOE distances from PDB structure file.

Uses idpconfgen libraries for coordinate parsing as it's proven
to be faster than BioPython.

Back-calculator logic inspired from X-EISD.
Error = 0.0001 as reported in Lincoff et al. 2020.

USAGE:
    $ spycipdb noe <PDB-FILES> [--exp-file]
    $ spycipdb noe <PDB-FILES> [--exp-file] [--output] [--ncores]

REQUIREMENTS:
    Experimental data must be comma-delimited with at least the following columns:
    
    res1,atom1,atom1_multiple_assignments,res2,atom2,atom2_multiple_assignments
    
    Where res1/atom1 is the atom number and name respectively for the first residue
    and res2/atom2 is the atom number and name respectively for the second residue.

OUTPUT:
    Output is in standard .JSON format as follows, with the first
    key-value pair being the reference formatting for residues and
    atom-names:
    
    {
        'format': { 'res1': [],
                    'atom1': [],
                    'atom1_multiple_assignments': [],
                    'res2': [],
                    'atom2': [],
                    'atom2_multiple_assignments': []
                    },
        'pdb1': [dist_values],
        'pdb2': [dist_values],
        ...
    }
"""
import json
import argparse
import shutil
import pandas as pd
from pathlib import Path
from functools import partial

from spycipdb import log
from spycipdb.libs import libcli
from spycipdb.logger import S, T, init_files, report_on_crash
from spycipdb.libs.libfuncs import get_scalar

from idpconfgen.libs.libio import extract_from_tar, read_path_bundle
from idpconfgen.libs.libmulticore import pool_function
from idpconfgen.libs.libstructure import(
    Structure,
    col_name,
    col_resSeq,
    )

LOGFILESNAME = '.spycipdb_noe'
_name = 'noe'
_help = 'NOE back-calculator given experimental data template.'

_prog, _des, _usage = libcli.parse_doc_params(__doc__)

ap = libcli.CustomParser(
    prog=_prog,
    description=libcli.detailed.format(_des),
    usage=_usage,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    )

libcli.add_argument_pdb_files(ap)
libcli.add_argument_exp_file(ap)
libcli.add_argument_output(ap)
libcli.add_argument_ncores(ap)

TMPDIR = '__tmppre__'
ap.add_argument(
    '--tmpdir',
    help=(
        'Temporary directory to store data during calculation '
        'if needed.'
        ),
    type=Path,
    default=TMPDIR,
    )


def get_exp_format_pre(fexp):
    format = {}
    exp = pd.read_csv(fexp)
    
    format['res1'] = exp.res1.values.astype(int).tolist()
    format['atom1'] = exp.atom1.values.tolist()
    format['atom1_multiple_assignments'] = exp.atom1_multiple_assignments.values.tolist()
    format['res2'] = exp.res2.values.astype(int).tolist()
    format['atom2'] = exp.atom2.values.tolist()
    format['atom2_multiple_assignments'] = exp.atom2_multiple_assignments.values.tolist()
    
    return format

