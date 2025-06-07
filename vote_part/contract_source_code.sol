// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

contract Vote {
    address private owner;
    uint public tournament_id;
    string creater_wallet_address;
    mapping(uint8 => uint16) public votes_per_candidate; // 후보자들이 받은 투표 수 (최대 2^16)
    mapping(string => bool) private voted_wallet_address; // 없는 key값에 접근하면 Default 값인 False return.

    constructor (uint id, string memory wallet_address) {
        owner = msg.sender;
        tournament_id = id;
        creater_wallet_address = wallet_address;
    }

    function isVoted(string memory wallet_address) public view returns (bool) {
        require(msg.sender == owner, "Only Server can call");
        return voted_wallet_address[wallet_address];
    }

    function vote(string memory wallet_address, uint8 candidate_id) external {
        require(msg.sender == owner, "Only Server can call");
        require(!isVoted(wallet_address));
        
        votes_per_candidate[candidate_id]++;
        voted_wallet_address[wallet_address] = true;
    }

    function getAllCandidatesVote(uint8 candidate_count) external view returns (uint16[] memory) {
        uint16[] memory votes = new uint16[](candidate_count);
        for (uint8 i = 0; i < candidate_count; i++) {
            votes[i] = votes_per_candidate[i];
        }
        return votes;
    }
}