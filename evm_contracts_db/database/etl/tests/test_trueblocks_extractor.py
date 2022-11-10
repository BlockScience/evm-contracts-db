import pytest

from evm_contracts_db.database.etl.trueblocks_extractor import TrueblocksExtractor


@pytest.mark.parametrize("query,result", [
    ({
        'function': 'list', 
        'value': ['0x01','0x02']
    },
    "chifra list 0x01 0x02"
    ),
    ({
        'function': 'export', 
        'value': '0x01', 
        'format': 'csv',
        'filepath': 'tmp/test.json'
    },
    "chifra export --fmt csv 0x01 > tmp/test.json"
    )
    ])
def test_build_chifra_command(query, result):

    tbe = TrueblocksExtractor()
    assert tbe.build_chifra_command(query) == result


def test_run_chifra_list():

    testQuery = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    
    tbe = TrueblocksExtractor()
    cmd = tbe.build_chifra_command(testQuery)
    result = tbe.run_chifra(cmd, parse_as='lines')

    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, list), f"Expected list, not {type(result)}"
    assert len(result) > 148, f"Fewer results found than expected... what gives?"
