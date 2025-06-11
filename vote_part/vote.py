from flask import Flask, request, jsonify
from web3 import Web3
import json
import os
from dotenv import load_dotenv
import hashlib
from collections import defaultdict
from solcx import compile_files, install_solc, set_solc_version
import json
import requests

# .env 파일에서 환경 변수 로드
'''
   ETHEREUM_NODE_URL=<이더리움 노드 URL>
   ADMIN_ADDRESS=<관리자 지갑 주소>
   PRIVATE_KEY=<관리자 개인키>
'''
load_dotenv(".env")

# 계정 설정
ethereum_node_url = os.getenv('ETHEREUM_NODE_URL')
deployer_account = os.getenv('ADMIN_ADDRESS') #w3.eth.accounts[0]
private_key = os.getenv('PRIVATE_KEY')

app = Flask(__name__)

# Web3 연결
w3 = Web3(Web3.HTTPProvider(ethereum_node_url))

def get_chain_id(rpc_url):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_chainId",
        "params": [],
        "id": 1
    }
    
    response = requests.post(rpc_url, json=payload)
    result = response.json()
    
    # 16진수를 10진수로 변환
    chain_id_hex = result['result']
    chain_id_decimal = int(chain_id_hex, 16)
    
    return chain_id_decimal

# Transaction 생성 시 필요한 ChainID 조회
chain_id = get_chain_id(ethereum_node_url)


# contract의 abi를 저장 및 조회
def load_contract_abi():
    with open('vote_part/ContractAbi.json', 'r') as f:
        return json.load(f)

contract_abi = load_contract_abi()['abi']

def save_contract_abi():
    with open('vote_part/ContractAbi.json', 'w') as f:
        temp = {"abi" : contract_abi}
        json.dump(temp, f)


def compile_contract():
    """
    Solidity 컨트랙트 컴파일
    """
    global contract_abi
    solc_version = os.getenv('SOLC_VERSION')

    install_solc(solc_version)
    set_solc_version(solc_version)

    print("=== 컨트랙트 컴파일 중... ===")
    
    try:
        compiled_sol = compile_files('vote_part/contract_source_code.sol',
                                     output_values=['abi', 'bin'],
                                     solc_version="0.8.26")
        contract_interface = compiled_sol['vote_part/contract_source_code.sol:Vote']
        print("컴파일 완료!")

        if not contract_abi:
            contract_abi = contract_interface['abi']
            save_contract_abi()
        
        return contract_interface

    except:
        print("컴파일 오류!")
        return None

def deploy_contract_with_transaction(tournament_id, wallet_address):
    """
        Transaction을 통한 컨트랙트 배포

        args:
            tournament_id : uint
            wallet_address : SHA256(wallet_address + Token) -> string
    """
    print("\n=== 컨트랙트 배포 Transaction 생성 ===")
    
    # 1. 컨트랙트 컴파일
    contract_interface = compile_contract()

    if not contract_interface:
        print("컴파일 오류로 인한 컨트랙트 배포 실패!")
        return None

    
    # 2. 컨트랙트 객체 생성
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # 3. 배포 Transaction 빌드
    print("배포 Transaction 빌드 중...")
    
    # 생성자 매개변수
    constructor_args = (tournament_id, wallet_address)
    '''
        tournament_id : uint
        wallet_address : SHA256(wallet_address + Token) -> string
    '''
    
    # Transaction 데이터 생성
    transaction = contract.constructor(*constructor_args).build_transaction({
        'chainId' : chain_id,
        'from': deployer_account,
        'gas': 2000000,  # 충분한 가스 설정
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count(deployer_account),
    })
    
    print(f"Transaction 정보:")
    print(f"  - From: {transaction['from']}")
    print(f"  - Gas: {transaction['gas']}")
    print(f"  - Gas Price: {w3.from_wei(transaction['gasPrice'], 'gwei')} Gwei")
    print(f"  - To: {transaction.get('to', 'None (Contract Creation)')}")
    print(f"  - Data 길이: {len(transaction['data'])} characters")
    
    # 4. Transaction 서명
    print("\nTransaction 서명 중...")
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    
    # 5. Transaction 전송
    print("Transaction 전송 중...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction Hash: {tx_hash.hex()}")
    
    # 6. Transaction 완료 대기
    print("Transaction 완료 대기 중...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # 7. 결과 출력
    print("\n=== 배포 완료! ===")
    print(f"Contract Address: {tx_receipt.contractAddress}")
    print(f"Block Number: {tx_receipt.blockNumber}")
    print(f"Gas Used: {tx_receipt.gasUsed}")
    print(f"Transaction Status: {'Success' if tx_receipt.status == 1 else 'Failed'}")
    
    return tx_receipt.contractAddress

def analyze_deployment_transaction(tx_hash):
    """
    배포 Transaction 상세 분석
    """
    print(f"\n=== Transaction 분석: {tx_hash} ===")
    
    # Transaction 정보 조회
    tx = w3.eth.get_transaction(tx_hash)
    tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
    
    print("Transaction 정보:")
    print(f"  - Hash: {tx.hash.hex()}")
    print(f"  - From: {tx['from']}")
    print(f"  - To: {tx.to}")  # Contract 생성 시 None
    print(f"  - Value: {w3.from_wei(tx.value, 'ether')} ETH")
    print(f"  - Gas: {tx.gas}")
    print(f"  - Gas Price: {w3.from_wei(tx.gasPrice, 'gwei')} Gwei")
    print(f"  - Input Data 길이: {len(tx.input)} bytes")
    
    print("\nTransaction Receipt:")
    print(f"  - Status: {tx_receipt.status}")
    print(f"  - Block Number: {tx_receipt.blockNumber}")
    print(f"  - Gas Used: {tx_receipt.gasUsed}")
    print(f"  - Contract Address: {tx_receipt.contractAddress}")
    print(f"  - Cumulative Gas Used: {tx_receipt.cumulativeGasUsed}")
    
    # Contract 생성 여부 확인
    if tx_receipt.contractAddress:
        print(f"\n✅ Contract 생성 성공!")
        print(f"   새로운 Contract 주소: {tx_receipt.contractAddress}")
        
        # 생성된 Contract 코드 확인
        contract_code = w3.eth.get_code(tx_receipt.contractAddress)
        print(f"   Contract 코드 길이: {len(contract_code)} bytes")
    else:
        print(f"\n❌ Contract 생성 실패")


def send_transaction(contract_function, from_account = deployer_account, private_key = private_key):
    """
    Contract 함수 호출 Transaction 전송 (EHT Call은 아님.)
    """
    transaction = contract_function.build_transaction({
        'from': from_account,
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': w3.eth.get_transaction_count(from_account),
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Transaction 완료 대기
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_hash


def make_token(tournament_id : int, user_wallet_address : str) -> str:
    key = int.from_bytes(b'B10cKCH4iN', 'little')
    xor_val = tournament_id ^ key
    xor_bytes = xor_val.to_bytes(16, 'little')
    hash_input = xor_bytes + user_wallet_address.encode()
    full_token = hashlib.sha256(hash_input).hexdigest()

    new_hash_input = (user_wallet_address + full_token[:4]).encode()

    return hashlib.sha256(new_hash_input).hexdigest()


def _init() -> bool:
    """
    Web3 연결 설정
    """
    global w3

    print("Web3 연결 중...")

    if not w3.is_connected():
        print("Web3 연결 실패!")
        while(not w3.is_connected()):
            print("Web3 연결 재시도 중..")
            w3 = Web3(Web3.HTTPProvider(ethereum_node_url))
    
    print("Web3 연결 성공!")
    print(f"현재 블록 번호: {w3.eth.block_number}")
    print(f"배포자 계정: {deployer_account}")
    print(f"계정 잔액: {w3.from_wei(w3.eth.get_balance(deployer_account), 'ether')} ETH")
    
    return True



@app.route('/vote', methods=['POST'])
def vote():
    '''
        tournament_id : uint256,
        contract_address : str,
        candidate_id : uint8,
        wallet_address : str
    '''
    tournament_id = int(request.form.get('tournament_id'))
    contract_address = request.form.get('contract_address')
    candidate_id = int(request.form.get('candidate_id'))
    user_wallet_address = request.form.get('wallet_address')

    wallet_address = make_token(tournament_id, user_wallet_address)
    
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        print("\n투표 Transaction 전송...")
        '''
            wallet_address : str,
            candidate_id : uint8
        '''
        tx_hash = send_transaction(
            contract.functions.vote(wallet_address, candidate_id),
            deployer_account,
            private_key
        )
        print(f"Transaction Hash: {tx_hash.hex()}")
        print("투표 Transaction 전송 완료!")

        return jsonify({"status" : "Success"}), 200

    except Exception as e:
        print(f"\n투표 Transaction 전송 중 오류 발생 : {e}")

        return jsonify({"status": "Failed"}), 500


@app.route('/isVoted', methods=['POST'])
def isVoted():
    '''
        tournament_id : uint8,
        contract_address : str,
        wallet_address : str
    '''
    tournament_id = int(request.form.get('tournament_id'))
    contract_address = request.form.get('contract_address')
    user_wallet_address = request.form.get('wallet_address')

    wallet_address = make_token(tournament_id, user_wallet_address)

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        '''
            wallet_address : str
        '''
        isvoted = contract.functions.isVoted(wallet_address).call()

        return jsonify({"status" : "Success", "isVoted" : isvoted}), 200

    except Exception as e:
        print(f"\n투표 여부 확인 중 오류 발생 : {e}")

        return jsonify({"status": "Failed", "isVoted" : None}), 500


@app.route('/results', methods=['POST'])
def results():
    '''
        contract_address : str,
        totalCandidateCount : uint8
    '''
    #tournament_id = request.form.get('tournament_id')
    contract_address = request.form.get('contract_address')
    total_candidate_count = int(request.form.get('totalCandidateCount'))

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        '''
            total_candidate_count : uint8
        '''
        votes_list = contract.functions.getAllCandidatesVote(total_candidate_count).call()

        return jsonify({"status" : "Success", "totalVotes" : votes_list}), 200

    except Exception as e:
        print(f"\n투표 여부 확인 중 오류 발생 : {e}")

        return jsonify({"status": "Failed", "totalVotes" : None}), 500


@app.route('/tournaments', methods=['POST'])
def make_tournament():
    '''
        tournament_id : uint256,
        wallet_address : str
    '''
    tournament_id = int(request.form.get('tournament_id'))
    user_wallet_address = request.form.get('wallet_address')

    wallet_address = make_token(tournament_id, user_wallet_address)

    try:
        contract_address = deploy_contract_with_transaction(tournament_id, wallet_address)

        return jsonify({"contract_address" : contract_address}), 200
    
    except Exception as e:
        print(f"\n월드컵 생성 중 오류 발생 : {e}")
        return jsonify({"contract_address" : None}), 500


if __name__ == "__main__":
    if _init():
        app.run(debug=True, port=9000)