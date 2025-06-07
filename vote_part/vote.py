from flask import Flask, request, jsonify
from web3 import Web3
import json
import os
from dotenv import load_dotenv
import hashlib
from collections import defaultdict
from solcx import compile_source, compile_files
import json

# .env 파일에서 환경 변수 로드
'''
   ETHEREUM_NODE_URL=<이더리움 노드 URL>
   ADMIN_ADDRESS=<관리자 지갑 주소>
   PRIVATE_KEY=<관리자 개인키>
'''
load_dotenv("./.env")

# 계정 설정
ethereum_node_url = os.getenv('ETHEREUM_NODE_URL')
deployer_account = os.getenv('ADMIN_ADDRESS') #w3.eth.accounts[0]
private_key = os.getenv('PRIVATE_KEY')

app = Flask(__name__)

# Web3 연결
w3 = Web3(Web3.HTTPProvider(ethereum_node_url))

def load_contract_abi():
    with open('vote_part/ContractAbi.json', 'r') as f:
        return json.load(f)

contract_abi = load_contract_abi()['abi']

def save_contract_abi():
    with open('vote_part/ContractAbi.json', 'w') as f:
        temp = {"abi" : contract_abi}
        json.dump(temp, f)


# Solidity 컨트랙트 소스 코드
contract_source_code = '''
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract Vote {
    address private owner;
    uint public tournament_id;
    string creater_wallet_address;
    mapping(uint8 => uint16) public votes_per_candidate;
    mapping(string => bool) private voted_wallet_address; // 없는 key값에 접근하면 Default 값인 False return.

    constructor (uint id, string memory wallet_address) {
        owner = msg.sender;
        tournament_id = id;
        creater_wallet_address = wallet_address;
    }

    function isVoted(string memory wallet_address) public view returns (bool) {
        require(msg.sender == owner, "Only Server can call");
        return voted_wallet_address[wallet_address];
        // for (uint i = 0; i < voted_wallet_address.length; i++) {
        //     if (keccak256(bytes(voted_wallet_address[i])) == keccak256(bytes(wallet_address))) {
        //         return true;
        //     }
        // }
    }

    function vote(string memory wallet_address, uint8 candidate_id) external {
        require(msg.sender == owner, "Only Server can call");
        require(!isVoted(wallet_address));
        
        votes_per_candidate[candidate_id]++;
        voted_wallet_address[wallet_address] = true;
        // emit voteEvent(tournament_id, creater_wallet_address, wallet_address, candidate_id);
    }
    
    // event voteEvent(uint tournamentId, bytes32 createrWalletAddress, bytes32 walletAddress, uint8 candidateId);
}
'''

def compile_contract():
    """
    Solidity 컨트랙트 컴파일
    """
    global contract_abi
    print("=== 컨트랙트 컴파일 중... ===")
    
    try:
        #compiled_sol = compile_source(contract_source_code)
        compiled_sol = compile_files('vote_part/contract_source_code.sol',
                                     solc_version="0.8.26")
        contract_interface = compiled_sol['<stdin>:SimpleStorage']
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
        return None, None

    
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
        'from': deployer_account,
        'gas': 2000000,  # 충분한 가스 설정
        'gasPrice': w3.to_wei('20', 'gwei'),
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
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
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
        'gasPrice': w3.to_wei('20', 'gwei'),
        'nonce': w3.eth.get_transaction_count(from_account),
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
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


def test_deployed_contract(contract_address, contract_abi=contract_abi):
    """
    배포된 Contract 테스트
    """
    print(f"\n=== 배포된 Contract 테스트 ===")
    
    # Contract 인스턴스 생성
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    
    # 1. 초기값 확인 (ETH Call - Transaction 아님)
    initial_value = contract.functions.getNumber().call()
    print(f"초기 저장값: {initial_value}")
    
    # 2. Owner 확인 (ETH Call - Transaction 아님)
    owner = contract.functions.owner().call()
    print(f"Contract Owner: {owner}")
    
    # 3. 값 변경 (Transaction 필요)
    print("\n값을 999로 변경하는 Transaction 전송...")
    tx_hash = send_transaction(
        contract.functions.setNumber(999),
        deployer_account,
        private_key
    )
    print(f"Transaction Hash: {tx_hash.hex()}")
    
    # 4. 변경된 값 확인 (ETH Call - Transaction 아님)
    new_value = contract.functions.getNumber().call()
    print(f"변경된 값: {new_value}")



def _init() -> bool:
    """
    Web3 연결 설정
    """
    if not w3.is_connected():
        print("Web3 연결 실패!")
        return False
    
    print("Web3 연결 성공!")
    print(f"현재 블록 번호: {w3.eth.block_number}")
    print(f"배포자 계정: {deployer_account}")
    print(f"계정 잔액: {w3.from_wei(w3.eth.get_balance(deployer_account), 'ether')} ETH")
    
    return True



@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()

    tournament_id = data['tournament_id']
    contract_address = data['contract_address']
    candidate_id = data['candidate_id']
    user_wallet_address = data['wallet_address']

    wallet_address = make_token(tournament_id, user_wallet_address)
    
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        print("\n투표 Transaction 전송...")
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
    data = request.get_json()

    tournament_id = data['tournament_id']
    contract_address = data['contract_address']
    user_wallet_address = data['wallet_address']

    wallet_address = make_token(tournament_id, user_wallet_address)

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        isvoted = contract.functions.isVoted(wallet_address).call()

        return jsonify({"status" : "Success", "isVoted" : isvoted}), 200

    except Exception as e:
        print(f"\n투표 여부 확인 중 오류 발생 : {e}")

        return jsonify({"status": "Failed", "isVoted" : None}), 500


@app.route('/results', methods=['POST'])
def results():
    data = request.get_json()

    tournament_id = data['tournament_id']
    contract_address = data['contract_address']
    total_candidate_count = data['totalCandidateCount']

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    try:
        votes_list = contract.functions.getAllCandidatesVote(total_candidate_count).call()

        return jsonify({"status" : "Success", "totalVotes" : votes_list}), 200

    except Exception as e:
        print(f"\n투표 여부 확인 중 오류 발생 : {e}")

        return jsonify({"status": "Failed", "totalVotes" : None}), 500


@app.route('/tournaments', methods=['POST'])
def make_tournament():
    data = request.get_json()

    tournament_id = data['tournament_id']
    user_wallet_address = data['wallet_address']

    wallet_address = make_token(tournament_id, user_wallet_address)

    contract_address = deploy_contract_with_transaction(tournament_id, wallet_address)

    return jsonify({"contract_address" : contract_address})


if __name__ == "__main__":
    if _init():
        app.run(debug=True, port=9000)