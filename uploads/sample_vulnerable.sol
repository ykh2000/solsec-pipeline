// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SampleVulnerable {
    mapping(address => uint256) public balances;

    // A classic reentrancy vulnerability for Slither to find
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount);
        
        // VULNERABILITY: External call before state update
        (bool success, ) = msg.sender.call{value: _amount}("");
        require(success);
        
        balances[msg.sender] -= _amount;
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}

