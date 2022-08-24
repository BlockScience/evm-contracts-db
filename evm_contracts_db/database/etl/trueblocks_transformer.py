import logging
from pprint import pformat

from utils.files import load_json, save_json
from utils.blockchain import load_txid
from utils.strings import camel_to_snake, could_be_address


class TrueblocksTransformer:

    def transform_chifra_trace_result(self, result):
        """From result of chifra traces, return list of nested dictionaries corresponding to unique transactions records"""

        txList = []
        data = result['data']
        data = [{**trace, 'transactionId': load_txid(trace['blockNumber'], trace['transactionIndex'])} for trace in data]

        # Group traces by transaction hash and extract relevant information
        uniqueTxs = list(set([trace['transactionId'] for trace in data]))
        for txId in uniqueTxs:
            txData = {'transaction_id': txId}
            traces = [t for t in data if t['transactionId'] == txId]

            # Get data on originating transaction
            _origin = [t for t in traces if t["traceAddress"] is None]
            if len(_origin) == 0:
                # I hope this never happens...
                logging.warning(f"Could not find a trace without a traceAddress for txn {txId}; expected 1. Skipping...")
                continue            
            elif len(_origin) > 1:
                # Not sure why this happens - don't see anything odd upon inspection of Trueblocks output.
                # When it finds two, it repeats the same one twice, so okay to proceed
                logging.warning(f"Found {len(_origin)} traces with no traceAddress for txn {txId}; expected 1. Using the first one found...")
            origin = _origin[0]
            for key in ['transactionHash', 'blockNumber']:
                txData[camel_to_snake(key)] = origin.get(key)
            for key in ['from', 'to']:
                txData[f"{key}_address"] = origin['action'][key]
            txData['value'] = origin['action']['value']

            aT = origin.get('articulatedTrace', {})
            txData['call_name'] = aT.get('name')
            txData['call_inputs'] = aT.get('inputs')
            txData['call_outputs'] = aT.get('outputs')

            # Get list of contracts created as a result of that transaction
            contractsCreated = []
            _creations = [t for t in traces if t.get('action', {}).get('callType', '') == 'creation']
            for trace in _creations:
                address = trace['result']['newContract']
                contractsCreated.append(address)
            txData['contracts_created'] = contractsCreated

            # BlockchainTransactionTrace model: Lump together remaining compressedTrace + output information, tacking on delegation if found
            # Warning: only captures the first iteration of call delegation! (not a deeper callstack)
            _calls = [t for t in traces if t.get('action', {}).get('callType', '') == 'call' and t["traceAddress"] is not None]
            _delegatecalls = [t for t in traces if t.get('action', {}).get('callType', '') == 'delegatecall' and t["traceAddress"] is not None]
            calls = []
            for trace in _calls:
                try:
                    call = {'id': f"{txId}.{trace['traceAddress']}"}
                    action = trace.get('action', {})
                    for key in ['from', 'to']:
                        call[f"{key}_address"] = action.get(key)
                    call['compressed_trace'] = trace.get('compressedTrace', "")
                    call['value'] = action.get('value')
                    call['error'] = trace.get('error')
                    call['outputs'] = trace.get('result', {}).get('output')
                    delegates = [
                        d['action']['to'] for d in _delegatecalls if (
                            d['action']['from'] == action.get('to') and
                            d.get('compressedTrace', "") == trace.get('compressedTrace', "") and
                            d['traceAddress'].startswith(trace['traceAddress'])
                        )
                    ]
                    call['delegate'] = delegates[0] if len(delegates) > 0 else None
                    calls.append(call)
                except KeyError as e:
                    logging.warning(e)
                    logging.debug(pformat(trace))
                    
            txData['traces'] = calls

            # Add transaction to list
            txList.append(txData)

        return txList

    def transform_chifra_transaction_result(self, result):
        """From result of chifra transactions, return list of nested dictionaries corresponding to unique transactions records
        Does not get contracts_created or traces!"""

        txList = []
        data = result.get('data')
        if data is None:
            logging.warning("'data' not found in transaction result")
            return []

        for tx in data:
            txId = load_txid(tx['blockNumber'], tx['transactionIndex'])
            txData = {
                'transaction_id': txId,
                'block_number': tx.get('blockNumber'),
                'transaction_hash': tx.get('hash'),
                'value': tx.get('value'),
            }
            for key in ['from', 'to']:
                txData[f"{key}_address"] = tx[key]

            # Get articulated trace data
            aT = tx.get('articulatedTx', {})
            txData['call_name'] = aT.get('name')
            txData['call_inputs'] = aT.get('inputs')
            txData['call_outputs'] = aT.get('outputs')

            # Get contract created
            contractCreated = tx.get('receipt', {}).get('contractAddress')
            if contractCreated is not None and contractCreated != '0x0':
                txData['contracts_created'] = [contractCreated]

            # Get events emitted by the 'to' address
            logs = []
            addresses_involved = [txData['from_address'], txData['to_address']] + txData.get('contracts_created', [])
            for log in tx.get('receipt', {}).get('logs', []):
                #if log['address'] == txData['to_address']:
                logData = {}
                logData['id'] = f"{txId}.{log['logIndex']}"
                logData['address'] = log['address']
                #topics = " ".join([t for t in log.get('topics', [])])
                #logData['topics'] = topics if len(topics) > 0 else None
                #logData['data'] = log.get('data)
                articulatedLog = log.get('articulatedLog', {})
                logData['event'] = articulatedLog.get('name')
                logData['compressed_log'] = log.get('compressedLog')
                logs.append(logData)

                # Add addresses to list
                addresses_involved.append(logData['address'])
                for value in articulatedLog.get('inputs', {}).values():
                    if could_be_address(value): # TODO: replace with actual address validity checker from web3 library
                        addresses_involved.append(value)
            if len(logs) > 0:
                txData['logs'] = logs

            txData['addresses_involved'] = list(set(addresses_involved))

            # Add transaction to list
            txList.append(txData)

        return txList