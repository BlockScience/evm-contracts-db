from evm_contracts_db.database.etl.trueblocks_extractor import TrueblocksExtractor
from evm_contracts_db.database.etl.trueblocks_transformer import TrueblocksTransformer
from evm_contracts_db.database.etl.trueblocks_loader import TrueblocksLoader


def test_save_chifra_trace_result():
    tbe = TrueblocksExtractor()
    tbt = TrueblocksTransformer()
    tbl = TrueblocksLoader()

    testQuery_list = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    cmd = tbe.build_chifra_command(testQuery_list)
    txIds = tbe.run_chifra(cmd, parse_as='lines')
    testQuery_trace = {
        'function': 'traces', 
        'value': txIds, 
        'format': 'json',
        'args': ['articulate']
    }    
    cmd = tbe.build_chifra_command(testQuery_trace)
    result = tbe.run_chifra(cmd, parse_as='json')
    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, dict), f"Expected list, not {type(result)}"
    
    parsed = tbt.transform_chifra_trace_result(result)
    assert len(parsed) == len(txIds), "Did not get traces of all transactions"

    tbl.insert_transactions(parsed)    
