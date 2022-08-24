from evm_contracts_db.database.etl.trueblocks_extractor import TrueblocksExtractor


def test_build_chifra_command():
    
    testQueries = [
        {'args': {
            'function': 'list', 
            'value': ['0x01', 
                      '0x02']
            },
         'result': "chifra list 0x01 0x02"
        },
        {'args': {
            'function': 'export', 
            'value': '0x01', 
            'format': 'csv',
            'filepath': 'tmp/test.json'
            },
         'result': "chifra export --fmt csv 0x01 > tmp/test.json"
        }
    ]

    tbe = TrueblocksExtractor()
    for i, q in enumerate(testQueries):
        assert tbe.build_chifra_command(q['args']) == q['result']
        print(f"Passed test build_chifra_command {i}")


def test_run_chifra():

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

    print("Passed test run_chifra")


if __name__ == "__main__":
    test_build_chifra_command()
    test_run_chifra()
