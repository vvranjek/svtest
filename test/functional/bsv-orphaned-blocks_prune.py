#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.


from test_framework.test_framework import BitcoinTestFramework, ChainManager
from test_framework.util import sync_blocks, connect_nodes, assert_equal, p2p_port
from test_framework.mininode import*
from test_framework import mininode



from bsv_pbv_common import (
    wait_for_waiting_blocks,
    wait_for_validating_blocks
)

from test_framework.blocktools import *





class OrphanedBlocks(BitcoinTestFramework):

    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.chain = ChainManager()
        #self.extra_args = [["-prune"]]




    def create_transaction_size(self, size, node):
        out_value = 100000000
        tx = CTransaction()

        script_tx = CScript([OP_RETURN] + [b"a" * size])
        tx.vout.append(CTxOut(out_value, script_tx))


        txHex = node.fundrawtransaction(ToHex(tx),{ 'changePosition' : len(tx.vout)})['hex']

        dec_tx = node.decoderawtransaction(txHex)
        print("Tx size: %s" % dec_tx["size"])
        #assert_equal(dec_tx["size"], size)

        txHex = node.signrawtransaction(txHex)['hex']
        tx = FromHex(CTransaction(), txHex)
        tx.rehash()
        node.sendrawtransaction(txHex)
        #node.generate(1)


    # Moves MPT time. Can't time travel in reverse
    def move_mpt_forward(self, mpt_set, node):
        # This function could be made more efficient, but it gets the job done in this simple form
        mpt = node.getblockheader(node.getbestblockhash())['mediantime']
        while (mpt < mpt_set):
            node.setmocktime(mpt_set)
            node.generate(1)
            mpt = node.getblockheader(node.getbestblockhash())['mediantime']

        assert_equal(mpt, mpt_set)


    # Create an empty block with given block time. Used to move median past time around
    def mine_empty_block(self, nTime):
        node = self.nodes[0]
        hashPrev = int(node.getbestblockhash(),16)

        coinbase = create_coinbase(node.getblockcount() + 1 )
        block = create_block(hashPrev, coinbase, nTime)
        block.nVersion = 3
        block.hashMerkleRoot = block.calc_merkle_root()
        block.rehash()
        block.solve()
        ret = node.submitblock(ToHex(block))
        print("Ret: %s" % ret)
        assert(ret is None)



    def mine_empty_block_hash(self, nTime, node, hash):
        #hashPrev = int(node.getbestblockhash(),16)
        hashPrev = hash

        print("Mining from hash %s" % hash)


        coinbase = create_coinbase(node.getblockcount() + 1 )
        block = create_block(hashPrev, coinbase, nTime)
        block.solve()
        ret = node.submitblock(ToHex(block))
        print("Ret: %s" % ret)
        assert(ret is None)

        block.rehash()
        return block.hash

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





    def reconsider_block(self):

        activation_time = 1546300800


        node1 = self.nodes[0]
        node2 = self.nodes[1]

        # test_node = mininode.NodeConnCB()
        def on_getdata(conn, message):
            print("GEEEEEEEEET DATAAAAAAAA")

        # test_node.on_getdata = on_getdata
        node1.connection.on_getdata = self.on_getdata
        node1.


        block_hash = int(node1.getbestblockhash(), 16)
        print("Best hash: %s" % block_hash)

        node1.generate(1)

        block_hash=int(node1.getbestblockhash(),16)
        print("Best hash: %s" % block_hash)

        mine_time=node1.getblock(node1.getbestblockhash())['time']

        # Generate 100 blocks
        for i in range(100):
            self.mine_empty_block_hash(nTime=mine_time+10, node=node1, hash=block_hash)
            block_hash = int(node1.getbestblockhash(), 16)
            mine_time = mine_time + 10


        # Create orphan block
        orphan_hash = block_hash
        orphan_hash = str(node1.getbestblockhash())
        orphan_hash_int = int(node1.getbestblockhash(), 16)
        print("Orphan hash: %s" % orphan_hash)









        #node1.invalidateblock(str(node1.getbestblockhash()))
        node1.invalidateblock(orphan_hash)









        # Mine after orphan created
        for i in range(10):
            self.mine_empty_block_hash(nTime=mine_time+10, node=node1, hash=int(node1.getbestblockhash(), 16))
            #self.mine_empty_block(nTime=activation_time)
            block_hash = int(node1.getbestblockhash(), 16)
            mine_time = mine_time + 10


        #node1.reconsiderblock(orp)
        node1.reconsiderblock(orphan_hash)
        node1.preciousblock(orphan_hash)

        #print(node1.getchaintips())

        solved_blocks = []
        block_hash = orphan_hash_int
        for i in range(10):
            block_hash = self.solve_block(nTime=mine_time + 10, node=node1, hash=block_hash)
            solved_blocks.append(block_hash)
            block_hash = int(block_hash.hash, 16)
            print("HHHAAAAasdasdasdasSK: %s" % block_hash)
            mine_time = mine_time + 10



        time.sleep(2)
        return Trueeeee

        block_hash = orphan_hash_int
        for i in range(10):
            blck = self.mine_empty_block_hash(nTime=mine_time + 10, node=node1, hash=block_hash)
            block_hash = int(blck.hash, 16)
            print("HHHAAAASK: %s" % block_hash)

            mine_time = mine_time + 10
            self.send_header_for_blocks(blck)





        print(node1.getchaintips())

        #print(node1.getchaintips()['hash'])



    def make_orphan_big_chain(self):
        time_deadline = 1546300800

        self.stop_node(0)
        self.start_node(0, extra_args=["-prune=1", "-preferredblockfilesize=16777216"])



        node1 = self.nodes[0]
        node2 = self.nodes[1]

        node1.generate(1000)




        #print("Moving time forward")
        #self.move_mpt_forward(mpt_set=1680127892, node=node1)
        #print("Done")



        for n in range(70):
            for i in range(2):
                self.create_transaction_size(size=500000, node=node1)
                node1.generate(1)

        node1.generate(1)
        orphan = node1.getblockhash(node1.getblockcount())
        print("Orphan hash: %s" % orphan)
        node1.invalidateblock(str(orphan))




        for n in range(70):
            for i in range(2):
                self.create_transaction_size(size=500000, node=node1)
                node1.generate(1)

        print("Done")


        print("Pruning")
        node1.pruneblockchain(10)
        print("Pruning done")


        blocks=node1.getblockcount()

        hash_5=node1.getblockhash(5)
        hash_201=node1.getblockhash(201)
        block_5=node1.getblock(hash_5)
        block_201=node1.getblock(hash_201)

        print("Block 5 size: %s" % block_5["size"])
        print("Block 5 size: %s" % block_201["size"])
        print("Block 5 size: %s" % node1.getblock(node1.getblockhash(blocks))["size"])



        return Falseeeeeee

        return True




        node0.generate(195)
        cur_time = int(time.time())
        node0.generate(5)


        block195 = int(node0.getblockhash(node0.getblockcount() - 5), 16)
        block196_1 = int(node0.getblockhash(node0.getblockcount() - 4), 16)


        print("Chain height: %s\n" %  node0.getblockcount())


        tip = int(self.nodes[0].getblockhash(self.nodes[0].getblockcount() - 5), 16)
        height = self.nodes[0].getblockcount()-5
        for i in range(6):
            block = create_block(tip, create_coinbase(height), cur_time+i)
            block.nVersion = 3
            block.hashMerkleRoot = block.calc_merkle_root()
            block.rehash()
            block.solve()
            block195 = block.sha256
            height += 1
            self.nodes[0].submitblock(ToHex(block))
            cur_time += 1

            sync_blocks(self.nodes)
            self.sync_all([self.nodes[0:1]])

            print("Chain heighttttt: %s" % node0.getblockcount())



        for i in range(6):
            self.mine_empty_block(cur_time+i)





        print("Chain height: %s\n" %  node0.getblockcount())

        node0.generate(10)

        print("Chain height: %s\n" %  node0.getblockcount())


        block196_2 = int(node0.getblockhash(node0.getblockcount() - 5), 16)


        print("Block196_1: %s" % block196_1)
        print("Block196_2: %s" % block196_2)





        return True




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
        self.chain.save_spendable_output()
        node0.send_message(msg_block(block))

        for i in range(194):
            block195 = self.chain.next_block(block_count)
            block_count += 1
            self.chain.save_spendable_output()
            node0.send_message(msg_block(block))




        # out = []
        # for i in range(100):
        #     out.append(self.chain.get_spendable_output())
        #



        return True




        #self.nodes[0].setexcessiveblock(self.excessive_block_size)
        #self.test.run()

        block_count = 0

        node = NodeConnCB()
        connection = NodeConn('127.0.0.1', p2p_port(0), self.nodes[0], node)
        node.add_connection(connection)



        NetworkThread().start()
        node.wait_for_verack()

        self.chain.set_genesis_hash(int(self.nodes[0].getbestblockhash(), 16))
        block = self.chain.next_block(block_count)
        block_count += 1
        self.chain.save_spendable_output()
        node.send_message(msg_block(block))

        for i in range(10):
            block = self.chain.next_block(block_count)
            block_count += 1
            #self.chain.save_spendable_output()
            node.send_message(msg_block(block))



        return True

    def get_tests(self):
        node = self.nodes[0]
        #self.chain.set_genesis_hash( int(node.getbestblockhash(), 16) )




        self.nodes[0].generate(200)



    def run_test(self):
        #self.make_orphan_big_chain()
        self.reconsider_block()

if __name__ == '__main__':
    OrphanedBlocks().main()
