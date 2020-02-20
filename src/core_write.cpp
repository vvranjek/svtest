// Copyright (c) 2009-2016 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "core_io.h"

#include "dstencode.h"
#include "primitives/transaction.h"
#include "script/script.h"
#include "script/script_num.h"
#include "script/standard.h"
#include "serialize.h"
#include "streams.h"
#include "util.h"
#include "utilmoneystr.h"
#include "utilstrencodings.h"
#include "rpc/server.h"

#include <univalue.h>

std::string FormatScript(const CScript &script) {
    std::string ret;
    CScript::const_iterator it = script.begin();
    opcodetype op;
    while (it != script.end()) {
        CScript::const_iterator it2 = it;
        std::vector<uint8_t> vch;
        if (script.GetOp2(it, op, &vch)) {
            if (op == OP_0) {
                ret += "0 ";
                continue;
            }

            if ((op >= OP_1 && op <= OP_16) || op == OP_1NEGATE) {
                ret += strprintf("%i ", op - OP_1NEGATE - 1);
                continue;
            }

            if (op >= OP_NOP && op <= OP_NOP10) {
                std::string str(GetOpName(op));
                if (str.substr(0, 3) == std::string("OP_")) {
                    ret += str.substr(3, std::string::npos) + " ";
                    continue;
                }
            }

            if (vch.size() > 0) {
                ret += strprintf("0x%x 0x%x ", HexStr(it2, it - vch.size()),
                                 HexStr(it - vch.size(), it));
            } else {
                ret += strprintf("0x%x ", HexStr(it2, it));
            }

            continue;
        }

        ret += strprintf("0x%x ", HexStr(it2, script.end()));
        break;
    }

    return ret.substr(0, ret.size() - 1);
}

const std::map<uint8_t, std::string> mapSigHashTypes = {
    {SIGHASH_ALL, "ALL"},
    {SIGHASH_ALL | SIGHASH_ANYONECANPAY, "ALL|ANYONECANPAY"},
    {SIGHASH_ALL | SIGHASH_FORKID, "ALL|FORKID"},
    {SIGHASH_ALL | SIGHASH_FORKID | SIGHASH_ANYONECANPAY,
     "ALL|FORKID|ANYONECANPAY"},
    {SIGHASH_NONE, "NONE"},
    {SIGHASH_NONE | SIGHASH_ANYONECANPAY, "NONE|ANYONECANPAY"},
    {SIGHASH_NONE | SIGHASH_FORKID, "NONE|FORKID"},
    {SIGHASH_NONE | SIGHASH_FORKID | SIGHASH_ANYONECANPAY,
     "NONE|FORKID|ANYONECANPAY"},
    {SIGHASH_SINGLE, "SINGLE"},
    {SIGHASH_SINGLE | SIGHASH_ANYONECANPAY, "SINGLE|ANYONECANPAY"},
    {SIGHASH_SINGLE | SIGHASH_FORKID, "SINGLE|FORKID"},
    {SIGHASH_SINGLE | SIGHASH_FORKID | SIGHASH_ANYONECANPAY,
     "SINGLE|FORKID|ANYONECANPAY"},
};

/**
 * Create the assembly string representation of a CScript object.
 * @param[in] script    CScript object to convert into the asm string
 * representation.
 * @param[in] fAttemptSighashDecode    Whether to attempt to decode sighash
 * types on data within the script that matches the format of a signature. Only
 * pass true for scripts you believe could contain signatures. For example, pass
 * false, or omit the this argument (defaults to false), for scriptPubKeys.
 */
std::string ScriptToAsmStr(const CScript& script,
                           const bool fAttemptSighashDecode)
{
    CStringWriter stringWriter;
    ScriptToAsmStr(script, stringWriter, fAttemptSighashDecode);
    return stringWriter.MoveOutString();
}

void ScriptToAsmStr(const CScript& script,
                    CTextWriter& textWriter,
                    const bool fAttemptSighashDecode)
{
    opcodetype opcode;
    std::vector<uint8_t> vch;
    CScript::const_iterator pc = script.begin();
    while (pc < script.end()) 
    {
        if (pc != script.begin()) 
        {
            textWriter.Write(" ");
        }

        if (!script.GetOp(pc, opcode, vch))
        {
            textWriter.Write("[error]");
            return;
        }

        if (0 <= opcode && opcode <= OP_PUSHDATA4)
        {
            if (vch.size() <= static_cast<std::vector<uint8_t>::size_type>(4))
            {
                textWriter.Write(strprintf("%d", CScriptNum(vch, false).getint()));
            }
            else
            {
                // the IsKnownOpReturn check makes sure not to try to decode
                // OP_RETURN data that may match the format of a signature
                if (fAttemptSighashDecode && !script.IsKnownOpReturn())
                {
                    std::string strSigHashDecode;
                    // goal: only attempt to decode a defined sighash type from
                    // data that looks like a signature within a scriptSig. This
                    // won't decode correctly formatted public keys in Pubkey or
                    // Multisig scripts due to the restrictions on the pubkey
                    // formats (see IsCompressedOrUncompressedPubKey) being
                    // incongruous with the checks in CheckSignatureEncoding.
                    uint32_t flags = SCRIPT_VERIFY_STRICTENC;
                    if (vch.back() & SIGHASH_FORKID)
                    {
                        // If the transaction is using SIGHASH_FORKID, we need
                        // to set the apropriate flag.
                        // TODO: Remove after the Hard Fork.
                        flags |= SCRIPT_ENABLE_SIGHASH_FORKID;
                    }
                    if (CheckSignatureEncoding(vch, flags, nullptr))
                    {
                        const uint8_t chSigHashType = vch.back();
                        if (mapSigHashTypes.count(chSigHashType))
                        {
                            strSigHashDecode =
                                "[" +
                                mapSigHashTypes.find(chSigHashType)->second +
                                "]";
                            // remove the sighash type byte. it will be replaced
                            // by the decode.
                            vch.pop_back();
                        }
                    }
                    HexStr(vch, textWriter);
                    textWriter.Write(strSigHashDecode);
                }
                else
                {
                    HexStr(vch, textWriter);
                }
            }
        }
        else
        {
            textWriter.Write(GetOpName(opcode));
        }
    }
}

std::string EncodeHexTx(const CTransaction& tx, const int serialFlags)
{
    CStringWriter stringWriter;
    EncodeHexTx(tx, stringWriter, serialFlags);
    return stringWriter.MoveOutString();
}

class CHexWriter
{
    CTextWriter& tw;
public:
    CHexWriter(CTextWriter& twIn) : tw(twIn) {}

    void write(const char* pch, size_t nSize)
    {
        HexStr(pch, pch + nSize, tw);
    }

    template <typename T> CHexWriter& operator<<(const T& obj)
    {
        // Serialize to this stream
        ::Serialize(*this, obj);
        return (*this);
    }
};

void EncodeHexTx(const CTransaction& tx, CTextWriter& writer, const int serialFlags)
{
    CHexWriter ssTx(writer);
    ssTx << tx;
}

void ScriptPubKeyToUniv(const CScript &scriptPubKey, bool fIncludeHex, bool isGenesisEnabled, UniValue &out) {
    txnouttype type;
    std::vector<CTxDestination> addresses;
    int nRequired;

    out.pushKV("asm", ScriptToAsmStr(scriptPubKey));
    if (fIncludeHex) {
        out.pushKV("hex", HexStr(scriptPubKey.begin(), scriptPubKey.end()));
    }

    if (!ExtractDestinations(scriptPubKey, isGenesisEnabled, type, addresses, nRequired)) {
        out.pushKV("type", GetTxnOutputType(type));
        return;
    }

    out.pushKV("reqSigs", nRequired);
    out.pushKV("type", GetTxnOutputType(type));

    UniValue a(UniValue::VARR);
    for (const CTxDestination &addr : addresses) {
        a.push_back(EncodeDestination(addr));
    }
    out.pushKV("addresses", a);
}

void TxToJSON(const CTransaction& tx,
              const uint256& hashBlock,
              bool utxoAfterGenesis,
              const int serializeFlags,
              CJSONWriter& entry,
              const std::optional<CBlockDetailsData>&  blockData)
{
    entry.writeBeginObject();

    entry.pushKV("txid", tx.GetId().GetHex());
    entry.pushKV("hash", tx.GetHash().GetHex());
    entry.pushKV("version", tx.nVersion);
    entry.pushKV("size", (int)::GetSerializeSize(tx, SER_NETWORK, PROTOCOL_VERSION));
    entry.pushKV("locktime", (int64_t)tx.nLockTime);

    entry.writeBeginArray("vin");
    for (size_t i = 0; i < tx.vin.size(); i++)
    {
        const CTxIn& txin = tx.vin[i];
        entry.writeBeginObject();
        if (tx.IsCoinBase())
        {
            entry.pushK("coinbase");
            entry.pushQuote(true, false);
            HexStr(txin.scriptSig.begin(), txin.scriptSig.end(), entry.getWriter());
            entry.pushQuote(false);
        }
        else
        {
            entry.pushKV("txid", txin.prevout.GetTxId().GetHex());
            entry.pushKV("vout", int64_t(txin.prevout.GetN()));
            entry.writeBeginObject("scriptSig");

            entry.pushK("asm");
            entry.pushQuote(true, false);
            ScriptToAsmStr(txin.scriptSig, entry.getWriter(), true);
            entry.pushQuote(false);

            entry.pushK("hex");
            entry.pushQuote(true, false);
            HexStr(txin.scriptSig.begin(), txin.scriptSig.end(), entry.getWriter());
            entry.pushQuote(false, false);

            entry.writeEndObject();
        }
        entry.pushKV("sequence", (int64_t)txin.nSequence, false);

        entry.writeEndObject(i < tx.vin.size() - 1);
    }
    entry.writeEndArray();

    entry.writeBeginArray("vout");
    for (size_t i = 0; i < tx.vout.size(); i++)
    {
        const CTxOut& txout = tx.vout[i];
        entry.writeBeginObject();

        entry.pushKVMoney("value", FormatMoney(txout.nValue));
        entry.pushKV("n", static_cast<int64_t>(i));

        entry.writeBeginObject("scriptPubKey");
        ScriptPublicKeyToJSON(txout.scriptPubKey, true, utxoAfterGenesis, entry);
        entry.writeEndObject(false);

        entry.writeEndObject(i < tx.vout.size() - 1);
    }

    entry.writeEndArray();

    if (!hashBlock.IsNull())
    {
        entry.pushKV("blockhash", hashBlock.GetHex());
    }

    if (blockData.has_value())
    {
        auto& blockDataVal = blockData.value();
        entry.pushKV("confirmations", blockDataVal.confirmations);
        if (blockDataVal.time.has_value())
        {
            entry.pushKV("time", blockDataVal.time.value());
            entry.pushKV("blocktime", blockDataVal.blockTime.value());
            entry.pushKV("blockheight", blockDataVal.blockHeight.value());
        }
    }

    // the hex-encoded transaction. used the name "hex" to be consistent with
    // the verbose output of "getrawtransaction".
    entry.pushK("hex");
    entry.pushQuote(true, false);
    EncodeHexTx(tx, entry.getWriter(), serializeFlags);
    entry.pushQuote(false, false);

    entry.writeEndObject(false);
}

void ScriptPublicKeyToJSON(const CScript& scriptPubKey,
                           bool fIncludeHex,
                           bool isGenesisEnabled,
                           CJSONWriter& entry) {
    txnouttype type;
    std::vector<CTxDestination> addresses;
    int nRequired;

    entry.pushK("asm");
    entry.pushQuote(true, false);
    ScriptToAsmStr(scriptPubKey, entry.getWriter());
    entry.pushQuote(false);
    if (fIncludeHex)
    {
        entry.pushK("hex");
        entry.pushQuote(true, false);
        HexStr(scriptPubKey.begin(), scriptPubKey.end(), entry.getWriter());
        entry.pushQuote(false);
    }

    if (!ExtractDestinations(scriptPubKey, isGenesisEnabled, type, addresses, nRequired))
    {
        entry.pushKV("type", GetTxnOutputType(type), false);
        return;
    }

    entry.pushKV("reqSigs", nRequired);
    entry.pushKV("type", GetTxnOutputType(type));

    entry.writeBeginArray("addresses");
    for (size_t i = 0; i < addresses.size(); i++)
    {
        const CTxDestination& addr = addresses[i];
        entry.pushV(EncodeDestination(addr), i < addresses.size() - 1);
    }
    entry.writeEndArray(false);
}