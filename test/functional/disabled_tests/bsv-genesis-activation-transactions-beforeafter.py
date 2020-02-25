#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
"""
Test genesis activation height when sending transactions.
Test accepts transaction that tries to spend transaction with OP_RETURN which was sent to mempool before genesis activation but was mined after genesis activation.

Scenario:
Genesis height is 102.
1. Current tip is on height 101.
2. Create and send transaction tx1 with OP_RETURN in the locking script.
3. Generate an empty block (height 102). Genesis is activated.
4. Create and send transaction tx2 with OP_TRUE in the unlocking that tries to spend tx1.
   This transaction is NOT rejected as bitcoind does not check if input transactions in mempool are spendable.
5. Generate new block with tx1 and tx2. It is on height 103 so it is not rejected.
"""
from test_framework.test_framework import ComparisonTestFramework
from test_framework.script import CScript, OP_RETURN, OP_TRUE, OP_ADD
from test_framework.blocktools import create_transaction
from test_framework.util import assert_equal, p2p_port
from test_framework.comptool import TestManager, TestInstance, RejectResult
from test_framework.mininode import msg_tx
from time import sleep

class BSVGenesisActivationTransactionsBeforeAfter(ComparisonTestFramework):

    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.genesisactivationheight = 102
        self.extra_args = [['-whitelist=127.0.0.1', '-genesisactivationheight=%d' % self.genesisactivationheight]]

    def run_test(self):
        self.test.run()

    def get_tests(self):

        # shorthand for functions
        block = self.chain.next_block
        node = self.nodes[0]
        self.chain.set_genesis_hash( int(node.getbestblockhash(), 16) )
        
        # Create a new block
        block(0)

        self.chain.save_spendable_output()

        yield self.accepted()

        # Now we need that block to mature so we can spend the coinbase.
        test = TestInstance(sync_every_block=False)
        for i in range(100):
            block(5000 + i)
            test.blocks_and_transactions.append([self.chain.tip, True])
            self.chain.save_spendable_output()
        yield test

        # collect spendable outputs now to avoid cluttering the code later on
        out = []
        for i in range(100):
            out.append(self.chain.get_spendable_output())

        # Create transaction with OP_RETURN in the locking script.
        tx1 = create_transaction(out[0].tx, out[0].n, b'', 100000, CScript([OP_RETURN]))
        self.test.connections[0].send_message(msg_tx(tx1))
        # wait for transaction processing
        sleep(1)

        # generate an empty block, height is 102
        block(1, spend=out[1])
        yield self.accepted()

        tx2 = create_transaction(tx1, 0, b'\x51', 1, CScript([OP_TRUE]))
        self.test.connections[0].send_message(msg_tx(tx2))
        # wait for transaction processing
        sleep(1)

        # Mine block (height 103) with new transactions.
        self.nodes[0].generate(1)
        tx = self.nodes[0].getblock(self.nodes[0].getbestblockhash())['tx']
        assert_equal(len(tx), 3)
        assert_equal(tx1.hash, tx[1])
        assert_equal(tx2.hash, tx[2])

if __name__ == '__main__':
    BSVGenesisActivationTransactionsBeforeAfter().main()
