#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.

from test_framework.mininode import *
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import p2p_port, disconnect_nodes
from test_framework.blocktools import create_block, create_coinbase, assert_equal

import contextlib
import datetime
import glob

# This tests checks scenario of logging about more honest peers.
# Scenario:
#    1. Peer1 creates new block b1 with height 2. After 5 seconds, it sends headers message.
#    2. Bitcoind sends GETDATA to peer1.
#    3. Peer1 sends block b1.
#    4. Peer2 creates new block b2 with height 2. Right after that, it sends headers message.
#    5. Bitcoind sends GETDATA to peer2.
#    6. Peer2 sends block b2.
#    7. Bitcoind logs that more honest block with the same height was received.

class LogTimeDiffTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.num_peers = 2

    def prepareBlock(self, height):
        tip = int("0x" + self.nodes[0].getbestblockhash(), 16)
        block_time = int(time.time())
        block = create_block(tip, create_coinbase(height=height, outputValue=25), block_time)
        block.solve()
        return block

    @contextlib.contextmanager
    def run_node_with_connections(self, title, node_index, args, number_of_connections):
        logger.debug("setup %s", title)

        self.start_node(node_index, args)

        connectionCbs = []
        for i in range(number_of_connections):
            connectionCbs.append(NodeConnCB())

        connections = []
        for connCb in connectionCbs:
            connection = NodeConn('127.0.0.1', p2p_port(0), self.nodes[node_index], connCb)
            connections.append(connection)
            connCb.add_connection(connection)

        thr = NetworkThread()
        thr.start()
        for connCb in connectionCbs:
            connCb.wait_for_verack()

        logger.debug("before %s", title)
        yield connections
        logger.debug("after %s", title)

        for connection in connections:
            connection.close()
        del connections
        # once all connection.close() are complete, NetworkThread run loop completes and thr.join() returns success
        thr.join()
        disconnect_nodes(self.nodes[node_index],1)
        self.stop_node(node_index)
        logger.debug("finished %s", title)

    def run_test(self):

        self.stop_node(0)

        with self.run_node_with_connections("logging difference between block created timestamp and header received timestamp", 0, [], 2) as p2p_connections:

            # initialize
            self.nodes[0].generate(1)

            connection1 = p2p_connections[0]
            connection2 = p2p_connections[1]

            # 1. create first block (creation time is set)
            block = self.prepareBlock(2)

            # 2. sleep five seconds
            time.sleep(5)

            # 3. connection1 sends HEADERS msg to bitcoind and waits for GETDATA (received time is set)
            headers_message = msg_headers()
            headers_message.headers = [CBlockHeader(block)]
            connection1.cb.send_message(headers_message)
            connection1.cb.wait_for_getdata(block.sha256)

            # 4. connection1 sends BLOCK
            connection1.cb.send_message(msg_block(block))

            # 5. create second block
            block = self.prepareBlock(2)

            # 6. connection2 sends HEADERS msg to bitcoind
            headers_message = msg_headers()
            headers_message.headers = [CBlockHeader(block)]
            connection2.cb.send_message(headers_message)

            # 7. connection2 waits for GETDATA and sends BLOCK
            connection2.cb.wait_for_getdata(block.sha256)
            connection2.cb.send_message(msg_block(block))

            # syncing
            connection1.cb.sync_with_ping()
            connection2.cb.sync_with_ping()

            # check log file for logging about block timestamp and received headers timestamp difference
            time_difference_log_found = False
            for line in open(glob.glob(self.options.tmpdir + "/node0" + "/regtest/bitcoind.log")[0]):
                if "Chain tip timestamp-to-received-time difference" in line:
                    time_difference_log_found = True
                    logger.info("Found line: %s", line)
                    break

            assert_equal(time_difference_log_found, True)

if __name__ == '__main__':
    LogTimeDiffTest().main()