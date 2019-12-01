# -*- coding: utf-8 -*-

# python std lib
import copy
import logging
import os
import re

# sgit imports
from sgit.exceptions import SgitConfigException

# 3rd party imports
import ruamel
from git import Repo
from ruamel import yaml


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Sgit(object):
    def __init__(self):
        self.sgit_config_file_name = '.sgit.yaml'

        self.sgit_config_file_path = os.path.join(
            os.getcwd(),
            self.sgit_config_file_name,
        )

    def init_repo(self):
        """
        Algorithm:
            - Check if .sgit.yaml exists
                - If exists:
                    - Exit out from script
                - If do not exists
                    - Write new initial empty file to disk
        """
        default_repo_content = "repos:\n"

        if os.path.exists(self.sgit_config_file_path):
            print(f"File '{self.sgit_config_file_name}' already exists on disk")
            return 1
        else:
            with open(self.sgit_config_file_path, 'w') as stream:
                stream.write(default_repo_content)
                print(f'Successfully wrote new config file "{self.sgit_config_file_name}" to disk')

    def _get_config_file(self):
        with open(self.sgit_config_file_path, 'r') as stream:
            return yaml.load(stream, Loader=ruamel.yaml.Loader)
            # TODO: Minimal required data should be 'repos:'
            #       Raise error if missing from loaded config

    def _dump_config_file(self, config_data):
        """
        Writes the entire config file to the given disk path set
        in the method constructor.
        """
        with open(self.sgit_config_file_path, 'w') as stream:
            yaml.dump(config_data, stream, indent=2, default_flow_style=False)

    def repo_list(self):
        config = self._get_config_file()
        repos = config.get('repos', {})

        print(f" ** All repos **")

        if not repos:
            print(f"  No repos found")
            return 1

        for repo_name, repo_data in repos.items():
            print(f"")
            print(f" - {repo_name}")
            print(f"   - URL: {repo_data.get('clone-url')}")
            print(f"   - Rev: {repo_data.get('revision')}")

    def repo_add(self, name, url, revision):
        if not name or not url or not revision:
            raise SgitConfigException(f'Name "{name}, url "{url}" or revision "{revision}" must be set')

        config = self._get_config_file()

        if name in config['repos']:
            print(f'Repo with name "{name}" already exists in config file')
            return 1

        config['repos'][name] = {
            'clone-url': url,
            'revision': revision,
        }

        self._dump_config_file(config)

    def repo_remove(self, name):
        if not name:
            raise SgitConfigException(f'Name "{name}" must be set to sometihng')

        config = self._get_config_file()

        if name not in config['repos']:
            print(f'No repo with name "{name}" found in config file')
            return 1

        del config['repos'][name]

        self._dump_config_file(config)

        print(f'Removed repo "{name}" from config file')

    def repo_set(self, name, attrib, value):
        if not attrib or not value:
            raise SgitConfigException(f'Attrib "{attrib}" or "{value}" must be set')

        config = self._get_config_file()

        if name not in config['repos']:
            print(f'Repo with name "{name}" not found in config file')
            return 1

        attrib_to_key_mapping = {
            'url': 'clone-url',
            'rev': 'revision',
        }

        key = attrib_to_key_mapping[attrib]

        config['repos'][name][key] = value

        self._dump_config_file(config)

        print(f'Updated key "{key}" in repo "{name}" to value -> "{value}"')

    def update(self, name):
        """
        Algorithm:
            - If the folder do not exists
                - clone the repo with Repo.clone_from
                - Update the rev to specified rev
            - If the folder do exists
                - If working_tree has any changes in it
                    - Throw error about working tree has changes
                - If working tree is empty
                    - Reset the repo to the specified rev
        """
        if not name:
            raise SgitConfigException(f'Name "{name}" must be set')

        config = self._get_config_file()

        if name not in config['repos']:
            print(f'Repo with name "{name}" not found in config file')
            return 1

        repo_path = os.path.join(os.getcwd(), name)
        revision = config['repos'][name]['revision']

        if not os.path.exists(repo_path):
            repo = Repo.clone_from(
                config['repos'][name]['clone-url'],
                repo_path,
                branch=revision,
            )
        else:
            print(f'TODO: Parse for any changes...')
            repo = Repo(
                os.path.join(os.getcwd(), name)
            )
            # TODO: Check that origin remote exists

            # Fetch all changes from upstream git repo
            repo.remotes.origin.fetch()

            # Ensure the local version of the branch exists and points to the origin ref for that branch
            repo.create_head(f'{revision}', f'origin/{revision}')

            # Checkout the selected revision
            # TODO: This only support branches for now
            repo.heads[revision].checkout()
