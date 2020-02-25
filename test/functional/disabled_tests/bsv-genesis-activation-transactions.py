#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
"""
Test genesis activation height when sending transactions.
Test accepts transaction that tries to spend transaction with OP_RETURN which was mined after genesis
and rejects transaction that tries to spend transaction with OP_RETURN which was mined before genesis.

Scenario:
Genesis height is 104.
1. Current height is 101.
2. Create and send transaction tx1 with OP_RETURN in the locking script (height 102).
3. Mine block (height 102) with new transaction tx1.
4. Create and send transaction tx2 with OP_TRUE in the unlocking that tries to spend tx1 (height 103).
5. Mine block (height 103). It should not contain tx2.
6. Create and send transaction tx3 with OP_RETURN in the locking script (height 104).
7. Create and send transaction tx4 with OP_TRUE in the unlocking that tries to spend tx3 (height 104).
8. Mine block (height 104). It should contain new transactions tx3 and tx4.
"""
from test_framework.test_framework import ComparisonTestFramework
from test_framework.script import CScript, OP_RETURN, OP_TRUE
from test_framework.blocktools import create_transaction
from test_framework.util import assert_equal, p2p_port
from test_framework.comptool import TestManager, TestInstance, RejectResult
from test_framework.mininode import msg_tx
from time import sleep

class BSVGenesisActivationTransactions(ComparisonTestFramework):

    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.genesisactivationheight = 104
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
        tx1 = create_transaction(out[1].tx, out[1].n, b"", 100000, CScript([OP_RETURN]))
        self.test.connections[0].send_message(msg_tx(tx1))
        # wait for transaction processing
        sleep(1)
        # Mine block (height 102) with new transaction.
        self.nodes[0].generate(1)
        # Obtain newly mined block. It should contain new transaction tx1.
        tx = self.nodes[0].getblock(self.nodes[0].getbestblockhash())['tx']
        assert_equal(len(tx), 2)
        assert_equal(tx1.hash, tx[1])
        self.log.info("Created transaction %s on height %d",
            tx1.hash, self.genesisactivationheight-2)

        # Create transaction with OP_TRUE in the unlocking that tries to spend tx1.
        tx2 = create_transaction(tx1, 0, b'\x51', 1, CScript([OP_TRUE]))
        self.test.connections[0].send_message(msg_tx(tx2))
        # wait for transaction processing
        sleep(1)
        # Mine block (height 103).
        self.nodes[0].generate(1)
        # Obtain newly mined block. It should NOT contain new transaction tx2.
        tx = self.nodes[0].getblock(self.nodes[0].getbestblockhash())['tx']
        assert_equal(len(tx), 1)
        self.log.info("Created transaction %s on height %d that tries to spend transaction on height %d",
            tx2.hash, self.genesisactivationheight-1, self.genesisactivationheight-2)

        # Create transaction with OP_RETURN in the locking script.
        tx3 = create_transaction(out[2].tx, out[2].n, b"", 100000, CScript([OP_RETURN]))
        self.test.connections[0].send_message(msg_tx(tx3))
        # Create transaction with OP_TRUE in the unlocking that tries to spend tx3.
        tx4 = create_transaction(tx3, 0, b'\x51', 1, CScript([OP_TRUE]))
        self.test.connections[0].send_message(msg_tx(tx4))
        # wait for transaction processing
        sleep(1)
        # Mine block (height 104) with new transactions.
        self.nodes[0].generate(1)
        # Obtain newly mined block. It should contain new transactions tx3 and tx4.
        tx = self.nodes[0].getblock(self.nodes[0].getbestblockhash())['tx']
        assert_equal(len(tx), 3)
        assert_equal(tx3.hash, tx[1])
        assert_equal(tx4.hash, tx[2])
        self.log.info("Created transactions %s and %s on height %d that tries to spend transaction on height %d",
            tx3.hash, tx4.hash, self.genesisactivationheight, self.genesisactivationheight)

if __name__ == '__main__':
    BSVGenesisActivationTransactions().main()
