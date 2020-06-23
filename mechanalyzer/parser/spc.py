"""
Read the mechanism file
"""

import os
import pandas
import automol
from mechanalyzer.parser.csv_ import csv_dct
from mechanalyzer.parser.csv_ import read_csv_headers


# Build a spc dct containing all info species input file
def build_spc_dct(spc_str, spc_type):
    """ Get a dictionary of all the input species
        indexed by InChi string
    """

    if spc_type == 'csv':
        spc_dct = csv_dct(spc_str)
    else:
        raise NotImplementedError

    return spc_dct


# SPC list from reactions
def build_queue(rxn_lst):
    """ Build spc queue from the reaction lst for the drivers
        :return spc_queue: all the species and corresponding models in rxn
        :rtype: list[(species, model),...]
    """

    if 'all' in rxn_lst:
        # First check if rxn_lst is a bunch of species
        spc_queue = rxn_lst['all']['species']
    else:
        # Build the list from expanding the reacs and prods
        spc_queue = []
        for rxn in rxn_lst:
            model = rxn['model']
            spc_queue.extend(((reac, model) for reac in rxn['reacs']))
            spc_queue.extend(((prod, model) for prod in rxn['prods']))

    return spc_queue


# Write new files
def write_stereo_csv(spc_str, outname='species_stereo.csv', path='.'):
    """ read the species file in a .csv format and write a new one
        that has stero information
    """

    # Read the headers
    headers = [header for header in read_csv_headers(spc_str)
               if header != 'name']
    if 'inchi' not in headers:
        headers.append('inchi')
    headers_noich = [header for header in headers
                     if header not in ('inchi', 'inchikey')]
    new_headers = ['inchi', 'inchikey'] + headers_noich

    # Read in the initial CSV information (deal with mult stereo)
    init_dct = csv_dct(spc_str, values=headers, key='name')

    # Build a new dict
    new_dct = {}
    for name in init_dct:

        # Get the inchi key
        ich = init_dct[name]['inchi']

        # Generate ichs with stereo and hashes
        ichs_wstereo = _generate_stereo(ich)

        # Add name and inchi info to string
        for idx, ich_wstereo in enumerate(ichs_wstereo):

            # Augment name if needed
            if idx == 0:
                sname = name
            else:
                sname = name + '-{}'.format(str(idx+1))

            # Initialize
            new_dct[sname] = {}

            # Generate hash key from InChI
            hashkey = automol.inchi.inchi_key(ich_wstereo)

            # Add vals to dct
            new_dct[sname].update({'inchi': ich_wstereo, 'inchikey': hashkey})

            for header in headers_noich:
                new_dct[sname][header] = init_dct[name][header]

    # Writer string
    spc_str = ','.join(['name'] + new_headers) + '\n'
    for name in new_dct:
        spc_str += '{},'.format(name)
        for idx, header in enumerate(new_headers):
            val = new_dct[name][header]
            if isinstance(val, str):
                val = "'{}'".format(val)
            spc_str += str(val)
            if idx+1 < len(new_headers):
                spc_str += ','
        spc_str += '\n'

    # Write the file
    stereo_file = os.path.join(path, outname)
    with open(stereo_file, 'w') as file_obj:
        file_obj.write(spc_str)


def _generate_stereo(ich):
    """ stereo
    """
    if not automol.inchi.is_complete(ich):
        # print('adding stereochemistry for {0}, {1}, {2}'.format(
        #            name, smi, ich))
        ichs = automol.inchi.add_stereo(ich)
    else:
        ichs = [ich]
    return ichs