#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
from time import sleep

from test_framework.test_framework import BitcoinTestFramework
from test_framework.blocktools import *
from test_framework.script import CScript, OP_RETURN, OP_FALSE, OP_TRUE

class MaxStandardTxSizeTest(BitcoinTestFramework):

    def set_test_params(self):
        self.num_nodes = 2
        self.maxStandardTxSizeDefault = 100000
        self.maxStandardTxSizeNew = 110000
        self.otherSize = 104 # TODO: This is supposedly the size of txSize-scriptSize. Not sure if this is a fixed value. Please double check
        self.time_deadline = 1546300800
        self.time_before = self.time_deadline - 40
        
    def setup_network(self):
        self.setup_clean_chain = True
        self.add_nodes(self.num_nodes)
    
    def mine_empty_block(self, nTime, node): 
        hashPrev = int(node.getbestblockhash(),16)

        coinbase = create_coinbase(node.getblockcount() + 1 )
        block = create_block(hashPrev, coinbase, nTime)
        block.solve()
        ret = node.submitblock(ToHex(block)) 
        assert(ret is None) 

    # Moves MPT time. Can't time travel in reverse
    def move_mpt_forward(self, mpt_set, node):
        # This function could be made more efficient, but it gets the job done in this simple form
        mpt = node.getblockheader(node.getbestblockhash())['mediantime']
        while (mpt < mpt_set):
            node.setmocktime(mpt_set)
            self.mine_empty_block(mpt_set, node)
            mpt = node.getblockheader(node.getbestblockhash())['mediantime']

        assert_equal(mpt, mpt_set)

    # Test for a failed or successful transaction
    def test_transaction(self, size, tx_pass, node):
        out_value = 10
        tx = CTransaction()

        script_tx = CScript([OP_RETURN] + [b"a" * (size - self.otherSize)])
        tx.vout.append(CTxOut(out_value, script_tx))

        if tx_pass == False:
            assert_raises_rpc_error(-4, "Transaction too large", node.fundrawtransaction,ToHex(tx))
        else:
            txHex = node.fundrawtransaction(ToHex(tx),{ 'changePosition' : len(tx.vout)})['hex']

            dec_tx = node.decoderawtransaction(txHex)
            assert_equal(dec_tx["size"], size)

            txHex = node.signrawtransaction(txHex)['hex']
            tx = FromHex(CTransaction(), txHex)
            tx.rehash()
            node.sendrawtransaction(txHex)
            node.generate(1)

    def test_from_cmdline(self):
        
        self.start_node(0, [])
        node = self.nodes[0]
        node.generate(101)

        # Check default value 100000
        self.test_transaction(size=self.maxStandardTxSizeDefault-1, tx_pass=True, node=self.nodes[0])
        self.test_transaction(size=self.maxStandardTxSizeDefault, tx_pass=False, node=self.nodes[0])

        # Set tx limit to 110000
        self.stop_node(0)
        # We need to set datacariersize to avoid scriptbubkey error on bigger transactions
        self.start_node(0, ['-datacarriersize=110000', "-maxstandardtxsize=%d" % self.maxStandardTxSizeNew, "-mocktime=%d" % self.time_before, "-reindex"])
        node = self.nodes[0]
        node.generate(101)

        # Move mpt just before deadline
        self.move_mpt_forward(mpt_set=self.time_deadline-1, node=node)
        self.test_transaction(size=self.maxStandardTxSizeDefault-1, tx_pass=True, node=self.nodes[0])
        self.test_transaction(size=self.maxStandardTxSizeDefault, tx_pass=False, node=self.nodes[0])

        # Move mpt after deadline
        self.move_mpt_forward(mpt_set=self.time_deadline+1, node=node)
        self.test_transaction(size=self.maxStandardTxSizeNew-1, tx_pass=True, node=self.nodes[0])
        self.test_transaction(size=self.maxStandardTxSizeNew, tx_pass=False, node=self.nodes[0])

        return True

    def test_from_rpc(self):
        
        self.stop_nodes()
        # We need to set datacariersize to avoid scriptpubkey error on bigger transactions
        self.start_node(1, ['-datacarriersize=110000', "-mocktime=%d" % self.time_before, "-reindex"])
        node = self.nodes[1]
        node.generate(101)

        # Check default value, ignore time, the default values should apply
        self.test_transaction(size=self.maxStandardTxSizeDefault-1, tx_pass=True, node=node)
        self.test_transaction(size=self.maxStandardTxSizeDefault, tx_pass=False, node=node)

        # Set tx limit to 110000
        node.setmaxstandardtxsize(self.maxStandardTxSizeNew)

        # Move mpt just before deadline
        self.move_mpt_forward(mpt_set=self.time_deadline-1, node=node)
        self.test_transaction(size=self.maxStandardTxSizeDefault-1, tx_pass=True, node=node)
        self.test_transaction(size=self.maxStandardTxSizeDefault, tx_pass=False, node=node)

        # Move mpt after deadline
        self.move_mpt_forward(mpt_set=self.time_deadline+1, node=node)
        self.test_transaction(size=self.maxStandardTxSizeNew-1, tx_pass=True, node=node)
        self.test_transaction(size=self.maxStandardTxSizeNew, tx_pass=False, node=node)

        return True

    def run_test(self):
        self.test_from_cmdline()
        self.test_from_rpc()

if __name__ == '__main__':
    MaxStandardTxSizeTest().main()

