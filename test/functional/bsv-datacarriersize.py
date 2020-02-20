#!/usr/bin/env python3
# Copyright (c) 2019 Bitcoin Association
# Distributed under the Open BSV software license, see the accompanying file LICENSE.
from time import sleep

from test_framework.cdefs import MAX_STANDARD_TX_SIZE
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from test_framework.mininode import *
from test_framework.script import CScript, OP_RETURN, OP_FALSE

# Test the functionality -datacarriersize works as expected. It should accept both OP_RETURN and OP_FALSE, OP_RETURN
# 1. Set -datacarriersize to 500B.
# 2. Send transaction with script that contains 500B. It should be accepted.
# 3. Send transaction with script that contains 501B. It should be rejected.

class DataCarrierSizeTest(BitcoinTestFramework):

    def set_test_params(self):
        self.num_nodes = 1
        self.num_peers = 1
        self.dataCarrierSize = 500;

    def setup_network(self):
        self.setup_nodes()

    def setup_nodes(self):
        self.add_nodes(self.num_nodes)
        self.start_node(0)

    

    def calc_needed_data_size(self,script_op_codes, target_size):
        def pushdata_size(sz):
            if sz < 0x4c: return 1  # OP_PUSHDATA
            elif sz <= 0xff: return 2  # OP_PUSHDATA1
            elif sz <= 0xffff: return 3  # OP_PUSHDATA2
            elif sz <= 0xffffffff: return 5 # OP_PUSHDATA4
            else: raise ValueError("Data too long to encode in a PUSHDATA op")

        return target_size - (len(script_op_codes) + pushdata_size(target_size))

    @staticmethod
    def _split_int(n, n_parts):
        rest = n
        step = n // n_parts
        for _ in range(n_parts-1):
            yield step
            rest -= step
        yield rest

    def fill_outputs(self, tx, n_outputs, script_op_codes, fund, total_bytes):
        for amount, n_bytes in zip(self._split_int(fund, n_outputs), self._split_int(total_bytes, n_outputs)):
            script = CScript(script_op_codes + [b"a" * self.calc_needed_data_size(script_op_codes, n_bytes)])
            assert len(script) == n_bytes
            tx.vout.append(CTxOut(amount, script))


    # creates transaction with n_outputs which cumulative size is total_bytes
    def make_tx_script_size(self, n_outputs, script_op_codes, fund, total_bytes):
        tx = CTransaction()
        self.fill_outputs(tx, n_outputs, script_op_codes, fund, total_bytes)
        tx_hex = self.nodes[0].fundrawtransaction(ToHex(tx), {'changePosition': 0})['hex']
        tx_hex = self.nodes[0].signrawtransaction(tx_hex)['hex']
        tx = FromHex(CTransaction(), tx_hex)
        tx.rehash()
        return tx

    # creates transaction with n_outputs, and size of the whole transaction of total_bytes. 
    # we try to create transactions multiple time, until we get exact size match
    def make_tx_total_size(self, n_outputs, script_op_codes, fund, total_bytes):

        while True:
            tx = CTransaction()
            # as we cannot call fundrawtransaction with transaction bigger than MAX_STANDARD_TX_SIZE
            # a bit smaller transacton is used to generate inputs
            self.fill_outputs(tx, n_outputs, script_op_codes, fund, total_bytes - 3000)
            tx_hex = self.nodes[0].fundrawtransaction(ToHex(tx), {'changePosition': 0})['hex']
            tx_hex = self.nodes[0].signrawtransaction(tx_hex)['hex']
            tx = FromHex(CTransaction(), tx_hex)

            #bytes needed to add to archive desired size
            missing_bytes = total_bytes - len(tx.serialize())

            desired_scripts_size = total_bytes - 3000 + missing_bytes

            del(tx.vout[1:])

            self.fill_outputs(tx, n_outputs, script_op_codes, fund, desired_scripts_size)

            tx_hex = self.nodes[0].signrawtransaction(ToHex(tx))['hex']
            tx = FromHex(CTransaction(), tx_hex)
            tx.rehash()
            final_size = len(tx.serialize())

            #signing transaction can change its lenght by +- n inputs
            #if tx size is not desired we will try again
            if final_size == total_bytes:
                return tx



    def check_datacarriersize(self, script_op_codes, n_outputs, dataCarrierSize, description):

        # dataCarrierSize parameter is used for checking the size of the whole script (CScript).
        with self.run_node_with_connections(description, 0, ['-datacarriersize=%d' % dataCarrierSize, '-acceptnonstdtxn=false'], self.num_peers) as connections:

            connection = connections[0]
            rejected_txs = []

            def on_reject(conn, msg):
                rejected_txs.append(msg)

            connection.cb.on_reject = on_reject

            # Create one transaction with size of dataCarrierSize
            tx_valid = self.make_tx_script_size(n_outputs, script_op_codes, 10000, dataCarrierSize)
            connection.send_message(msg_tx(tx_valid))

            # and one with one byte too many
            tx_invalid = self.make_tx_script_size(n_outputs, script_op_codes, 10000, dataCarrierSize + 1)
            connection.send_message(msg_tx(tx_invalid))

            # Wait for rejection.
            connection.cb.wait_for_reject()

            # Only second transaction should be rejected.
            assert_equal(len(rejected_txs), 1)
            assert_equal(rejected_txs[0].data, tx_invalid.sha256)
            assert_equal(rejected_txs[0].reason, b'datacarrier-size-exceeded')

    def check_max_standard_tx_size(self, script_op_codes, n_outputs, description):

        with self.run_node_with_connections(description, 0, ['-datacarriersize=%d' % (MAX_STANDARD_TX_SIZE * 2), '-acceptnonstdtxn=false'], self.num_peers) as connections:

            connection = connections[0]
            rejected_txs = []

            def on_reject(conn, msg):
                rejected_txs.append(msg)

            connection.cb.on_reject = on_reject

            # Create one transaction with a byte less than MAX_STANDARD_TX_SIZE
            tx_valid = self.make_tx_total_size(n_outputs, script_op_codes,
                                               10000, MAX_STANDARD_TX_SIZE - 1)
            connection.send_message(msg_tx(tx_valid))

            # and one with MAX_STANDARD_TX_SIZE
            tx_invalid = self.make_tx_total_size(n_outputs, script_op_codes,
                                                 10000, MAX_STANDARD_TX_SIZE)
            connection.send_message(msg_tx(tx_invalid))

            # Wait for rejection.
            connection.cb.wait_for_reject()

            # Only second transaction should be rejected.
            assert_equal(len(rejected_txs), 1)
            assert_equal(rejected_txs[0].data, tx_invalid.sha256)
            assert_equal(rejected_txs[0].reason, b'tx-size')


    def run_test(self):

        self.nodes[0].generate(101)
        self.stop_node(0)

        dataCarrierSize = 500
        self.check_datacarriersize([OP_RETURN]          , 1, dataCarrierSize, "script with one OP_RETURN op code")
        self.check_datacarriersize([OP_FALSE, OP_RETURN], 1, dataCarrierSize, "script with one OP_FALSE, OP_RETURN op code")
        self.check_datacarriersize([OP_RETURN]          , 3, dataCarrierSize, "script with three OP_RETURN op codes")
        self.check_datacarriersize([OP_FALSE, OP_RETURN], 3, dataCarrierSize, "script with three OP_FALSE, OP_RETURN op codes")

        self.stop_node(0)
        self.check_max_standard_tx_size([OP_RETURN]          , 1, "script with one OP_RETURN op code")
        self.check_max_standard_tx_size([OP_FALSE, OP_RETURN], 3, "script with three OP_FALSE, OP_RETURN op codes")

if __name__ == '__main__':
    DataCarrierSizeTest().main()

