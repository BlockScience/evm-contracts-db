import os
import json
import subprocess
import logging


class TrueblocksExtractor:
    """Run chifra commands and extract, transform, and load the outputs of these
    e.g., `chifra traces --articulate --fmt json [addresses]` 

    To support setups other than a single machine, probably want to switch to
    the REST api: https://trueblocks.io/api/
    """

    def build_chifra_command(self, params):
        """Build a chifra command to run by subprocess
        
        params: dictionary with the following keys:
            function: e.g., list, export
            value: single value or list of values to provide to command (e.g., address(es), transaction(s))
            format: (optional) e.g., csv, json
            args: (optional) list of flags to provide
            kwargs: (optional) dictionary of other keyword:value pairs for chifra
            postprocess: (optional) string corresponding to command line postprocessing commands
            filepath: (optional) provide file path to pipe output to
        """

        assert ('function' in params.keys()) and ('value' in params.keys()), "Provide both a function and a value"

        # Get required arguments
        fcn = params['function']
        addresses = params['value']
        if isinstance(addresses, list):
            addresses = " ".join(addresses)

        # Set optional arguments
        postprocess = params.get('postprocess', None)

        # Set export format if provided
        if params.get('format', None) is not None:
            format = f"--fmt {params['format']}"
        else:
            format = None

        # Add flags
        if params.get('args', None) is not None:
            argsList = [f"--{f.strip('-')}" for f in params.get('args')]
        else:
            argsList = []

        # Add keyword arguments if provided
        if params.get('kwargs', None) is not None:
            kwargsList = [f"--{k.strip('-')} {v}" for k, v in params.get('kwargs').items()]
        else:
            kwargsList = []

        # Pipe output to file if filepath provided
        if params.get('filepath', None) is not None:
            pipeTo = f"> {params['filepath']}"
        else:
            pipeTo = None

        # Build list
        argList = ["chifra", fcn, *argsList, *kwargsList, addresses]
        if format:
            argList.insert(-1, format)
        if postprocess:
            argList.append(postprocess)
        if pipeTo:
            argList.append(pipeTo)
        
        # Return string to send to subprocess
        return " ".join(argList)

    def run_chifra(self, command, mode='w', parse_as='json', fpath=None):
        """Call chifra command and return the output as a JSON object

        command: chifra call as you would provide in command line
        parse_as: try to load the result as JSON or as a list of items, one on 
            each line
        mode: overwrite or append to file
        fpath: save output to a specified filepath, or pass False to suppress 
            file save (otherwise, saves to default JSON file)
        """

        DEFAULT_PATH = 'tmp/trueblocks.log'

        assert parse_as in ['json', 'lines'], "Only 'json' and 'lines' (e.g., for result of chifra list) are supported parse_as values"
        if fpath is None:
            fpath = DEFAULT_PATH
        elif fpath is False:
            fpath = None

        # Redirect output to fpath using pipe 
        if '>' not in command and fpath is not None:
            if 'w' in mode:
                m = ''
            elif 'a' in mode:
                m = ' -a'
            command = command + f"| tee{m} {fpath}"
        else:
            fpath = command.split('>')[-1]
            logging.warning(f"Command already pipes output to {fpath}: will not change this")

        try:
            # Run command and parse output as either JSON or a list of lines
            # NOTE: excapes all backslashes to prevent invalid \escape JSONDecoderError
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            result_lines = [line.decode('utf-8', errors='replace').replace('\\','\\\\') for line in process.stdout]

            if parse_as == 'json': 
                result_str = "".join(result_lines)
                try:
                    result = json.loads(result_str)
                except json.decoder.JSONDecodeError:
                    logging.warning("Could not parse chifra result as JSON")
                    result = None

            elif parse_as == 'lines':
                result = [s.strip() for s in result_lines]

        except Exception as e:
            logging.error(e)
            result = None

        return result

    def get_txids(self, address):
        """Get list of all transaction IDs for an address from the index"""

        query_list = {
            'function': 'list', 
            'value': address, 
            'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
        }
        
        cmd = self.build_chifra_command(query_list)
        txIds, _ = self.run_chifra(cmd, parse_as='lines')

        return txIds
