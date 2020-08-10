#! /usr/bin/env python

import subprocess
import argparse
import sys
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('-rt', '--repo_tag')
parser.add_argument('-b', '--bash', action='store_true')
parser.add_argument('-s', '--stop', action='store_true')
parser.add_argument('-ru', '--remove_unused', action='store_true')
args = parser.parse_args()


def unix_command(cmd_str, print_command=True, print_response=False):
    if print_command:
        print(cmd_str)
    cmd = cmd_str.split(' ')
    resp = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    if print_response and len(resp) > 0:
        resp_list = resp.strip().split('\n')
        for line in resp_list:
            print(line)
    return resp


def docker_command_response(cmd, return_df=True):
    resp = unix_command(cmd).strip().split('\n')
    col_line = resp[0]
    columns = [x.strip() for x in col_line.split('  ') if len(x) > 0]
    starts = [col_line.find(col) for col in columns]
    lines = []
    for line in resp[1:]:
        line_items = []
        for start in starts:
            line_items += [line[start:].split(' ')[0]]

        lines += [tuple(line_items)]
    if return_df:
        df = pd.DataFrame(lines)
        df.columns = columns
        return df
    else:
        return lines


def bash_in_docker(repo_tag):
    df = docker_command_response('docker container ls')
    df = df[df['IMAGE'] == repo_tag]
    if len(df) == 1:
        cmd = f'docker exec -it {df["NAMES"][0]} bash'
        print(cmd)
        os.system(cmd)
    elif len(df) > 1:
        print(f'More than one container has repo:tag == {repo_tag}')
        print(df)
    else:
        print(f'No containers found with repo:tag == {repo_tag}')


def stop_container(repo_tag):
    try:
        df = docker_command_response('docker container ls')
    except ValueError:
        print('No running containers')
        return
    df_c = df[df['IMAGE'] == repo_tag]
    if len(df_c) == 1:
        cid = df_c['CONTAINER ID'].iloc[0]
        unix_command(f'docker stop {cid}')
    elif len(df_c) > 1:
        print(f'More than one container with image {repo_tag} found')
        print(df_c)
    else:
        print(f'Image "{repo_tag}" not found in running containers')


def remove_unnamed_images():
    df = docker_command_response('docker image ls')
    unnamed = df[(df['REPOSITORY'] == '<none>') & (df['TAG'] == '<none>')]['IMAGE ID']
    for image in unnamed:
        unix_command(f'docker rmi {image} --force', print_response=True)


if args.stop:
    repo_tag = args.repo_tag
    stop_container(repo_tag=repo_tag)

if args.remove_unused:
    remove_unnamed_images()

if args.bash:
    repo_tag = args.repo_tag
    bash_in_docker(repo_tag=repo_tag)

