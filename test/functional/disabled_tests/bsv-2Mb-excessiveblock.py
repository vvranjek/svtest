#!/usr/bin/env python3
# Copyright (c) 2015-2016 The Bitcoin Core developers
# Copyright (c) 2017 The Bitcoin developers
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
"""
This test checks that if a peer send and excessive block size, it will get banned.
After the banned time has passed, the connection will be able to retablished.
"""

from test_framework.test_framework import ComparisonTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error
from test_framework.comptool import TestManager, TestInstance, RejectResult, logger
from test_framework.blocktools import *
import time
from test_framework.script import *
from test_framework.cdefs import (ONE_MEGABYTE)

class BSV128MBlocks(ComparisonTestFramework):

    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.excessive_block_size = 2 * ONE_MEGABYTE
        # Set arguments to run a bitcoind node with excessive blocksize 2Mb and banning time 10 seconds
        self.extra_args = [["-excessiveblocksize=%d" % self.excessive_block_size, "-blockmaxsize=%d" % self.excessive_block_size, "-bantime=10"]]

    def add_options(self, parser):
        super().add_options(parser)

    def run_test(self):
        self.nodes[0].setexcessiveblock(self.excessive_block_size)
        self.test.run()

    def get_tests(self):
        node = self.nodes[0]
        self.chain.set_genesis_hash( int(node.getbestblockhash(), 16) )

        # shorthand for functions
        block = self.chain.next_block

        # Create a new block
        block(0)
        self.chain.save_spendable_output()
        yield self.accepted()

        # Now we need that block to mature so we can spend the coinbase.
        test = TestInstance(sync_every_block=False)
        for i in range(99):
            block(5000 + i)
            test.blocks_and_transactions.append([self.chain.tip, True])
            self.chain.save_spendable_output()
        yield test

        # collect spendable outputs now to avoid cluttering the code later on
        out = []
        for i in range(100):
            out.append(self.chain.get_spendable_output())

        # Sending maximal size blocks will not cause disconnection neither banning (still be able to reconnect)
        block(1, spend=out[0], block_size=self.excessive_block_size)
        yield self.accepted()
        assert(not self.test.test_nodes[0].closed)
        self.test.clear_all_connections()
        self.test.add_all_connections(self.nodes)
        NetworkThread().start()
        self.test.wait_for_verack(5)

        # Sending oversized blocks will cause disconnection and banning (not able to reconnect within 10 seconds of bantime)
        assert(not self.test.test_nodes[0].closed)
        block(2, spend=out[1], block_size=self.excessive_block_size + 1)
        assert_equal(len(self.nodes[0].listbanned()),0)# Before, there are zero banned node
        self.test.connections[0].send_message(msg_block((self.chain.tip)))
        self.test.wait_for_disconnections()
        assert(self.test.test_nodes[0].closed)# disconnected
        assert(len(self.nodes[0].listbanned())>0)# After, list of banned nodes is not empty
        logger.info("Banned node : {}".format(self.nodes[0].listbanned()))

        # Test to reconnect after being banned
        self.restart_network()
        has_been_banned=False
        try:
            self.test.wait_for_verack(5)
        except:
            has_been_banned=True
        assert(has_been_banned)
        logger.info("Test banning excessive block size : PASS")

        time.sleep(10)#make sure at least 10 seconds (bantime) has passed
        assert_equal(len(self.nodes[0].listbanned()),0)# Make sure the banned register has been cleared
        # Rewind bad block and reconnect to node
        self.chain.set_tip(1)
        self.test.clear_all_connections()
        self.test.add_all_connections(self.nodes)
        NetworkThread().start()
        self.test.wait_for_verack(5)

        # Check we can still mine a good size block
        block(3, spend=out[1], block_size=self.excessive_block_size)
        yield self.accepted()

if __name__ == '__main__':
    BSV128MBlocks().main()
