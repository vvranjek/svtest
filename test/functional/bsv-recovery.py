#!/usr/bin/env python3
# Copyright (c) 2017 The Bitcoin Core developers
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
"""An example functional test

The module-level docstring should include a high-level description of
what the test is doing. It's the first thing people see when they open
the file and should give the reader information about *what* the test
is testing and *how* it's being tested
"""
# Imports should be in PEP8 ordering (std library first, then third party
# libraries then local imports).
from collections import defaultdict

# Avoid wildcard * imports if possible
from test_framework.blocktools import (create_block, create_coinbase)
from test_framework.mininode import (
    CInv,
    NetworkThread,
    NodeConn,
    NodeConnCB,
    mininode_lock,
    msg_block,
    msg_getdata,
)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
    connect_nodes,
    p2p_port,
    wait_until,
    get_auth_cookie,
)


from test_framework.mininode import*
from test_framework import mininode







import time

from test_framework.blocktools import (create_block, create_coinbase)
from test_framework.key import CECKey
from test_framework.mininode import (CBlockHeader,
                                     COutPoint,
                                     CTransaction,
                                     CTxIn,
                                     CTxOut,
                                     NetworkThread,
                                     NodeConn,
                                     NodeConnCB,
                                     msg_block,
                                     msg_headers)
from test_framework.script import (CScript, OP_TRUE)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (p2p_port, assert_equal)

# NodeConnCB is a class containing callbacks to be executed when a P2P
# message is received from the node-under-test. Subclass NodeConnCB and
# override the on_*() methods if you need custom behaviour.


class BaseNode(NodeConnCB):
    def __init__(self):
        """Initialize the NodeConnCB

        Used to inialize custom properties for the Node that aren't
        included by default in the base class. Be aware that the NodeConnCB
        base class already stores a counter for each P2P message type and the
        last received message of each type, which should be sufficient for the
        needs of most tests.

        Call super().__init__() first for standard initialization and then
        initialize custom properties."""
        super().__init__()
        # Stores a dictionary of all blocks received
        self.block_receive_map = defaultdict(int)

class ExampleTest(BitcoinTestFramework):
    # Each functional test is a subclass of the BitcoinTestFramework class.

    # Override the set_test_params(), add_options(), setup_chain(), setup_network()
    # and setup_nodes() methods to customize the test setup as required.

    def set_test_params(self):
        """Override test parameters for your individual test.

        This method must be overridden and num_nodes must be exlicitly set."""
        self.setup_clean_chain = True
        self.num_nodes = 1
        # Use self.extra_args to change command-line arguments for the nodes
        #self.extra_args = [["-rpcuser=Povrhnica", "-rpcpassword=Zla71#ep", "addnode=127.0.0.1:8331"]]
        #self.extra_args = [["-rpcuser=Povrhnica", "-rpcpassword=Zla71#ep"]]



    def setup_network(self):
        """Setup the test network topology

        Often you won't need to override this, since the standard network topology
        (linear: node0 <-> node1 <-> node2 <-> ...) is fine for most tests.

        If you do override this method, remember to start the nodes, assign
        them to self.nodes, connect them and then sync."""

        self.setup_nodes()
        self.stop_node(0)
        #self.start_node(0)
        self.start_node(0, extra_args=["-rpcuser=Povrhnica", "-rpcpassword=1234"])
        #self.start_node(0, extra_args=["-rpcport=8331"])

        # In this test, we're not connecting node2 to node0 or node1. Calls to
        # sync_all() should not include node2, since we're not expecting it to
        # sync.
        #connect_nodes(self.nodes[0], 1)
        #self.sync_all([self.nodes[0:1]])

    # Use setup_nodes() to customize the node start behaviour (for example if
    # you don't want to start all nodes at the start of the test).
    # def setup_nodes():
    #     pass


    def solve_block(self, nTime, node, hash):
        # hashPrev = int(node.getbestblockhash(),16)
        hashPrev = hash

        print("Solving from hash %s" % hash)

        coinbase = create_coinbase(node.getblockcount() + 1)
        block = create_block(hashPrev, coinbase, nTime)
        block.solve()
        # ret = node.submitblock(ToHex(block))
        #print("Ret: %s" % ret)
        #assert (ret is None)

        block.rehash()
        return block

    def send_header_for_blocks(self, new_blocks):
        headers_message = msg_headers()
        headers_message.headers = [CBlockHeader(b) for b in new_blocks]
        self.send_message(headers_message)


    def run_test(self):
        """Main test logic"""

        print(get_auth_cookie(self.nodes[0].datadir))

        #node_0=self.nodes[0].cli('-rpcuser=%s' % user, '-stdinrpcpass', input=password).getblockcount()
        node_0=self.nodes[0]



        # Create a P2P connection to one of the nodes
        node0 = BaseNode()
        connections = []
        connections.append(
            NodeConn('127.0.0.1', 8331, self.nodes[0], node0, net="mainnet"))
        node0.add_connection(connections[0])


        # Start up network handling in another thread. This needs to be called
        # after the P2P connections have been created.
        NetworkThread().start()
        # wait_for_verack ensures that the P2P connection is fully up.
        node0.wait_for_verack()



        print(node_0.getblockcount())


        return "True"


        for i in range(10):
            # Use the mininode and blocktools functionality to manually build a block
            # Calling the generate() rpc is easier, but this allows us to exactly
            # control the blocks and transactions.
            block = create_block(
                self.tip, create_coinbase(height), self.block_time)
            block.solve()
            block_message = msg_block(block)
            # Send message is used to send a P2P message to the node over our NodeConn connection
            node0.send_message(block_message)
            self.tip = block.sha256
            blocks.append(self.tip)
            self.block_time += 1
            height += 1

        self.log.info(
            "Wait for node1 to reach current tip (height 11) using RPC")
        self.nodes[1].waitforblockheight(11)

        self.log.info("Connect node2 and node1")
        connect_nodes(self.nodes[1], 2)

        self.log.info("Add P2P connection to node2")
        node2 = BaseNode()
        connections.append(
            NodeConn('127.0.0.1', p2p_port(2), self.nodes[2], node2))
        node2.add_connection(connections[1])
        node2.wait_for_verack()

        self.log.info(
            "Wait for node2 reach current tip. Test that it has propagated all the blocks to us")


        node_2 = self.nodes[2]


        def on_getdata(conn, message):

            #[conn.send_message(r)
            # for r in self.block_store.get_blocks(message.inv)]
            #[conn.send_message(r)
            # for r in self.tx_store.get_transactions(message.inv)]

            #for i in message.inv:
            #    if i.type == 1:
            #        self.tx_request_map[i.hash] = True
            #    elif i.type == 2:
            #        self.block_request_map[i.hash] = True
            print("GEEEEEEEEET DATAAAAAAAA %s" % message )
            #message.block


        node2.on_getdata = on_getdata

        node_2.generate(200)

        best_hash = int(node_2.getbestblockhash(), 16)
        mine_time = node_2.getblock(node_2.getbestblockhash())['time']
        print("Best hash: %s" % best_hash)

        # Solve blocks
        solved_blocks = []
        block_hash = best_hash
        for i in range(2):
            block_hash = self.solve_block(nTime=mine_time + 10, node=node_2, hash=block_hash)
            solved_blocks.append(block_hash)
            block_hash = int(block_hash.hash, 16)
            print("HHHAAAAasdasdasdasSK: %s" % block_hash)
            mine_time = mine_time + 10

        time.sleep(2)

        node2.send_header_for_blocks(solved_blocks)




        time.sleep(4)
        return Trueee



        getdata_request = msg_getdata()
        for block in blocks:
            getdata_request.inv.append(CInv(2, block))
        node2.send_message(getdata_request)

        # wait_until() will loop until a predicate condition is met. Use it to test properties of the
        # NodeConnCB objects.
        wait_until(lambda: sorted(blocks) == sorted(
            list(node2.block_receive_map.keys())), timeout=5, lock=mininode_lock)

        self.log.info("Check that each block was received only once")
        # The network thread uses a global lock on data access to the NodeConn objects when sending and receiving
        # messages. The test thread should acquire the global lock before accessing any NodeConn data to avoid locking
        # and synchronization issues. Note wait_until() acquires this global lock when testing the predicate.
        with mininode_lock:
            for block in node2.block_receive_map.values():
                assert_equal(block, 1)


if __name__ == '__main__':
    ExampleTest().main()
