#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
"""
Testing that we correctly reorg to longer chain even if we are still validating blocks
on lower chains

We have the following case:
     1
   /   \
  2     5
 / \    |
3  4    6
        |
        7

First we make chain 1->2, then we send 3,4 for parallel validation
While validating 3,4 we send competing chain 5->6->7
We should reorg to 7 even if we are still validating 3,4

After we reorged to 7 we finish validations of 3,4 and 7
should still be active
"""
from test_framework.mininode import (
    NetworkThread,
    NodeConn,
    NodeConnCB,
    msg_block,
)
from test_framework.test_framework import BitcoinTestFramework, ChainManager
from test_framework.util import (
    assert_equal,
    p2p_port
)
from bsv_pbv_common import (
    wait_for_waiting_blocks,
    wait_for_validating_blocks
)


class PBVReorg(BitcoinTestFramework):

    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.chain = ChainManager()
        self.extra_args = [["-whitelist=127.0.0.1"]]

    def run_test(self):
        block_count = 0

        # Create a P2P connections
        node0 = NodeConnCB()
        connection = NodeConn('127.0.0.1', p2p_port(0), self.nodes[0], node0)
        node0.add_connection(connection)

        NetworkThread().start()
        # wait_for_verack ensures that the P2P connection is fully up.
        node0.wait_for_verack()

        self.chain.set_genesis_hash(int(self.nodes[0].getbestblockhash(), 16))
        block = self.chain.next_block(block_count)
        block_count += 1
        node0.send_message(msg_block(block))

        for i in range(200):
            block = self.chain.next_block(block_count)
            block_count += 1
            node0.send_message(msg_block(block))

        self.log.info("waiting for block height 101 via rpc")
        self.nodes[0].waitforblockheight(200)

        tip_block_num = block_count-5

        # left branch
        self.chain.set_tip(tip_block_num)
        block2 = self.chain.next_block(block_count)
        block_count += 1
        node0.send_message(msg_block(block2))
        self.log.info(f"block2 hash: {block2.hash}")



if __name__ == '__main__':
    PBVReorg().main()
