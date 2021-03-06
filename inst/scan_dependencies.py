#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2018 Martin Ueding <dev@martin-ueding.de>

import argparse
import collections
import copy
import glob
import os
import pprint
import re
import subprocess

import yaml
import jinja2

pattern_load = re.compile(r'^pv_load\([\'"]([^\'"]+)[\'"], ([^()]+)\)', re.M)
pattern_depend = re.compile(r'^# Depend: (.*)$', re.M)
pattern_save = re.compile(r'^(?:pv_save|pv_call)\([\'"]([^\'"]+)[\'"], ([^(),]+)[,)]', re.M)

root_dirs = ['paramval', 'vignettes']

source_dir = os.path.dirname(__file__)


def resolve_path(match):
    cluster, varname = match
    return os.path.normpath('output/{}/{}.Rdata'.format(cluster, varname))


def process_file(filename, cluster):
    with open(filename) as f:
        contents = f.read()

    loads = list([resolve_path(match) for match in pattern_load.findall(contents)])
    saves = list([resolve_path(match) for match in pattern_save.findall(contents)])

    depends = [os.path.normpath(elem)
               for g in pattern_depend.findall(contents)
               for elem in glob.glob(g)]

    basename = os.path.basename(filename)
    barename = os.path.splitext(basename)[0]

    data = dict(filename=os.path.normpath(filename),
                basename=basename.replace('-', '_'),
                barename=barename.replace('-', '_'),
                loads=loads,
                saves=saves,
                depends=depends,
                loads_depends=loads + depends)

    return data


def add_rdata(barenames):
    return ['output/{}.Rdata'.format(x) for x in barenames]


edit_warning = 'This file is automatically created, do not edit by hand.'


def present_name(name):
    relative = os.path.normpath(os.path.relpath(name))
    return '"{}"'.format(relative)


def present_file_dict(file_dict):
    fdc = copy.deepcopy(file_dict)
    fdc['filename'] = present_name(fdc['filename'])
    fdc['basename'] = present_name(fdc['basename'])
    fdc['loads'] = list(map(present_name, fdc['loads']))
    fdc['saves'] = list(map(present_name, fdc['saves']))
    fdc['depends'] = list(map(present_name, fdc['depends']))
    fdc['loads_depends'] = list(map(present_name, fdc['loads_depends']))
    return fdc


def present_file_dicts(file_dicts):
    return list(map(present_file_dict, file_dicts))


def get_clusters():
    clusters = ['.']

    for root_dir in root_dirs:
        for it in os.scandir(root_dir):
            if it.is_dir():
                if not it.name in clusters:
                    clusters.append(it.name)

    return clusters


def get_templates():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(source_dir))

    templates = dict(
        dot=env.get_template('paramvalf-data-flow.dot.j2'),
        make=env.get_template('paramvalf-dependencies.mak.j2'),
        sh=env.get_template('paramvalf-run.j2'),
    )

    return templates


def process_cluster(cluster, templates):
    # Find the user written files.
    files_paramval = [process_file(filename, cluster) for filename in glob.glob('paramval/{}/*.R'.format(cluster))]
    files_rmd = [process_file(filename, cluster) for filename in glob.glob('vignettes/{}/*.Rmd'.format(cluster))]

    dot_rendered = templates['dot'].render(files=present_file_dicts(files_paramval),
                                           rmds=present_file_dicts(files_rmd),
                                           edit_warning=edit_warning)

    output_path = os.path.join('output', cluster)
    os.makedirs(output_path, exist_ok=True)

    dot_path = os.path.join(output_path, 'paramvalf-data-flow.dot')
    dot_rendered_path = os.path.join(output_path, 'paramvalf-data-flow.pdf') 

    with open(dot_path, 'w') as f:
        f.write(dot_rendered)
    subprocess.check_call(['dot', '-T', 'pdf', dot_path, '-o', dot_rendered_path])

    make = [dict(dest=f['saves'],
                 src=[f['filename']] + f['loads'],
                 depends=f['depends'],
                 task='Rscript -e "options(paramvalf_verbose = TRUE); source(\'$<\')"')
            for f in files_paramval]

    for f in files_rmd:
        make.append(dict(
            dest=['vignettes/{}/{}.pdf'.format(cluster, f['barename'])],
            src=[f['filename']] + f['loads'],
            task='Rscript -e "rmarkdown::render(\'{}\')"'.format(f['filename'])))

    make_all = [dest
                for item in make
                for dest in item['dest']]

    make_rendered = templates['make'].render(
        make=make,
        all=make_all,
        source_dir=source_dir,
        edit_warning=edit_warning)

    with open(os.path.join(output_path, 'paramvalf-dependencies.mak'), 'w') as f:
        f.write(make_rendered)

    state = dict(files_R=files_paramval,
                 files_rmd=files_rmd)

    with open(os.path.join(output_path, 'paramvalf-dependencies.yml'), 'w') as f:
        yaml.dump(state, f, default_flow_style=False)


def main():
    options = _parse_args()

    clusters = get_clusters()
    templates = get_templates()

    for cluster in clusters:
        process_cluster(cluster, templates)

    sh_rendered = templates['sh'].render(source_dir=source_dir, edit_warning=edit_warning)
    sh_rendered_path = 'paramvalf-run'
    with open(sh_rendered_path, 'w') as f:
        f.write(sh_rendered)
    os.chmod(sh_rendered_path, 0o755)


def _parse_args():
    '''
    Parses the command line arguments.

    :return: Namespace with arguments.
    :rtype: Namespace
    '''
    parser = argparse.ArgumentParser(description='')
    options = parser.parse_args()

    return options


if __name__ == '__main__':
    main()
