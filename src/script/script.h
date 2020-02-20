// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2016 The Bitcoin Core developers
// Copyright (c) 2018-2019 Bitcoin Association
// Distributed under the Open BSV software license, see the accompanying file LICENSE.

#ifndef BITCOIN_SCRIPT_SCRIPT_H
#define BITCOIN_SCRIPT_SCRIPT_H

#include "crypto/common.h"
#include "prevector.h"
#include "serialize.h"
#include "consensus/consensus.h"

#include <cassert>
#include <climits>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

// Maximum number of bytes pushable to the stack -- replaced with DEFAULT_STACK_MEMORY_USAGE after Genesis
static const unsigned int MAX_SCRIPT_ELEMENT_SIZE_BEFORE_GENESIS = 520;

// Maximum number of elements on the stack -- replaced with DEFAULT_STACK_MEMORY_USAGE after Genesis
static const unsigned int MAX_STACK_ELEMENTS_BEFORE_GENESIS = 1000;

// Threshold for nLockTime: below this value it is interpreted as block number,
// otherwise as UNIX timestamp. Thresold is Tue Nov 5 00:53:20 1985 UTC
static const unsigned int LOCKTIME_THRESHOLD = 500000000;

template <typename T> std::vector<uint8_t> ToByteVector(const T &in) {
    return std::vector<uint8_t>(in.begin(), in.end());
}

/** Script opcodes */
enum opcodetype {
    // push value
    OP_0 = 0x00,
    OP_FALSE = OP_0,
    OP_PUSHDATA1 = 0x4c,
    OP_PUSHDATA2 = 0x4d,
    OP_PUSHDATA4 = 0x4e,
    OP_1NEGATE = 0x4f,
    OP_RESERVED = 0x50,
    OP_1 = 0x51,
    OP_TRUE = OP_1,
    OP_2 = 0x52,
    OP_3 = 0x53,
    OP_4 = 0x54,
    OP_5 = 0x55,
    OP_6 = 0x56,
    OP_7 = 0x57,
    OP_8 = 0x58,
    OP_9 = 0x59,
    OP_10 = 0x5a,
    OP_11 = 0x5b,
    OP_12 = 0x5c,
    OP_13 = 0x5d,
    OP_14 = 0x5e,
    OP_15 = 0x5f,
    OP_16 = 0x60,

    // control
    OP_NOP = 0x61,
    OP_VER = 0x62,
    OP_IF = 0x63,
    OP_NOTIF = 0x64,
    OP_VERIF = 0x65,
    OP_VERNOTIF = 0x66,
    OP_ELSE = 0x67,
    OP_ENDIF = 0x68,
    OP_VERIFY = 0x69,
    OP_RETURN = 0x6a,

    // stack ops
    OP_TOALTSTACK = 0x6b,
    OP_FROMALTSTACK = 0x6c,
    OP_2DROP = 0x6d,
    OP_2DUP = 0x6e,
    OP_3DUP = 0x6f,
    OP_2OVER = 0x70,
    OP_2ROT = 0x71,
    OP_2SWAP = 0x72,
    OP_IFDUP = 0x73,
    OP_DEPTH = 0x74,
    OP_DROP = 0x75,
    OP_DUP = 0x76,
    OP_NIP = 0x77,
    OP_OVER = 0x78,
    OP_PICK = 0x79,
    OP_ROLL = 0x7a,
    OP_ROT = 0x7b,
    OP_SWAP = 0x7c,
    OP_TUCK = 0x7d,

    // splice ops
    OP_CAT = 0x7e,
    OP_SPLIT = 0x7f,   // after monolith upgrade (May 2018)
    OP_NUM2BIN = 0x80, // after monolith upgrade (May 2018)
    OP_BIN2NUM = 0x81, // after monolith upgrade (May 2018)
    OP_SIZE = 0x82,

    // bit logic
    OP_INVERT = 0x83,
    OP_AND = 0x84,
    OP_OR = 0x85,
    OP_XOR = 0x86,
    OP_EQUAL = 0x87,
    OP_EQUALVERIFY = 0x88,
    OP_RESERVED1 = 0x89,
    OP_RESERVED2 = 0x8a,

    // numeric
    OP_1ADD = 0x8b,
    OP_1SUB = 0x8c,
    OP_2MUL = 0x8d,
    OP_2DIV = 0x8e,
    OP_NEGATE = 0x8f,
    OP_ABS = 0x90,
    OP_NOT = 0x91,
    OP_0NOTEQUAL = 0x92,

    OP_ADD = 0x93,
    OP_SUB = 0x94,
    OP_MUL = 0x95,
    OP_DIV = 0x96,
    OP_MOD = 0x97,
    OP_LSHIFT = 0x98,
    OP_RSHIFT = 0x99,

    OP_BOOLAND = 0x9a,
    OP_BOOLOR = 0x9b,
    OP_NUMEQUAL = 0x9c,
    OP_NUMEQUALVERIFY = 0x9d,
    OP_NUMNOTEQUAL = 0x9e,
    OP_LESSTHAN = 0x9f,
    OP_GREATERTHAN = 0xa0,
    OP_LESSTHANOREQUAL = 0xa1,
    OP_GREATERTHANOREQUAL = 0xa2,
    OP_MIN = 0xa3,
    OP_MAX = 0xa4,

    OP_WITHIN = 0xa5,

    // crypto
    OP_RIPEMD160 = 0xa6,
    OP_SHA1 = 0xa7,
    OP_SHA256 = 0xa8,
    OP_HASH160 = 0xa9,
    OP_HASH256 = 0xaa,
    OP_CODESEPARATOR = 0xab,
    OP_CHECKSIG = 0xac,
    OP_CHECKSIGVERIFY = 0xad,
    OP_CHECKMULTISIG = 0xae,
    OP_CHECKMULTISIGVERIFY = 0xaf,

    // expansion
    OP_NOP1 = 0xb0,
    OP_CHECKLOCKTIMEVERIFY = 0xb1,
    OP_NOP2 = OP_CHECKLOCKTIMEVERIFY,
    OP_CHECKSEQUENCEVERIFY = 0xb2,
    OP_NOP3 = OP_CHECKSEQUENCEVERIFY,
    OP_NOP4 = 0xb3,
    OP_NOP5 = 0xb4,
    OP_NOP6 = 0xb5,
    OP_NOP7 = 0xb6,
    OP_NOP8 = 0xb7,
    OP_NOP9 = 0xb8,
    OP_NOP10 = 0xb9,

    // The first op_code value after all defined opcodes
    FIRST_UNDEFINED_OP_VALUE,

    // template matching params
    OP_SMALLINTEGER = 0xfa,
    OP_PUBKEYS = 0xfb,
    OP_PUBKEYHASH = 0xfd,
    OP_PUBKEY = 0xfe,

    OP_INVALIDOPCODE = 0xff,
};

const char *GetOpName(opcodetype opcode);
std::ostream& operator<<(std::ostream&, const opcodetype&);

class CScriptNum;

typedef prevector<28, uint8_t> CScriptBase;

/** Serialized script, used inside transaction inputs and outputs */
class CScript : public CScriptBase {
protected:
    CScript &push_int64(int64_t);

public:
    CScript() {}
    CScript(const_iterator pbegin, const_iterator pend)
        : CScriptBase(pbegin, pend) {}
    CScript(std::vector<uint8_t>::const_iterator pbegin,
            std::vector<uint8_t>::const_iterator pend)
        : CScriptBase(pbegin, pend) {}
    CScript(const uint8_t *pbegin, const uint8_t *pend)
        : CScriptBase(pbegin, pend) {}

    ADD_SERIALIZE_METHODS;

    template <typename Stream, typename Operation>
    inline void SerializationOp(Stream &s, Operation ser_action) {
        READWRITE(static_cast<CScriptBase &>(*this));
    }

    CScript &operator+=(const CScript &b) {
        insert(end(), b.begin(), b.end());
        return *this;
    }

    friend CScript operator+(const CScript &a, const CScript &b) {
        CScript ret = a;
        ret += b;
        return ret;
    }

    CScript(int64_t b) { operator<<(b); }

    explicit CScript(opcodetype b) { operator<<(b); }
    explicit CScript(const CScriptNum &b) { operator<<(b); }
    explicit CScript(const std::vector<uint8_t> &b) { operator<<(b); }

    CScript &operator<<(int64_t b) { return push_int64(b); }

    CScript &operator<<(opcodetype opcode) {
        if (opcode < 0 || opcode > 0xff)
            throw std::runtime_error("CScript::operator<<(): invalid opcode");
        insert(end(), uint8_t(opcode));
        return *this;
    }

    CScript &operator<<(const CScriptNum &);

    CScript &operator<<(const std::vector<uint8_t> &b) {
        if (b.size() < OP_PUSHDATA1) {
            insert(end(), uint8_t(b.size()));
        } else if (b.size() <= 0xff) {
            insert(end(), OP_PUSHDATA1);
            insert(end(), uint8_t(b.size()));
        } else if (b.size() <= 0xffff) {
            insert(end(), OP_PUSHDATA2);
            uint8_t data[2];
            WriteLE16(data, b.size());
            insert(end(), data, data + sizeof(data));
        } else {
            insert(end(), OP_PUSHDATA4);
            uint8_t data[4];
            WriteLE32(data, b.size());
            insert(end(), data, data + sizeof(data));
        }
        insert(end(), b.begin(), b.end());
        return *this;
    }

    CScript &operator<<(const CScript &b) {
        // I'm not sure if this should push the script or concatenate scripts.
        // If there's ever a use for pushing a script onto a script, delete this
        // member fn.
        assert(!"Warning: Pushing a CScript onto a CScript with << is probably "
                "not intended, use + to concatenate!");
        return *this;
    }

    bool GetOp(iterator &pc, opcodetype &opcodeRet,
               std::vector<uint8_t> &vchRet) {
        // Wrapper so it can be called with either iterator or const_iterator.
        const_iterator pc2 = pc;
        bool fRet = GetOp2(pc2, opcodeRet, &vchRet);
        pc = begin() + (pc2 - begin());
        return fRet;
    }

    bool GetOp(iterator &pc, opcodetype &opcodeRet) {
        const_iterator pc2 = pc;
        bool fRet = GetOp2(pc2, opcodeRet, nullptr);
        pc = begin() + (pc2 - begin());
        return fRet;
    }

    bool GetOp(const_iterator &pc, opcodetype &opcodeRet,
               std::vector<uint8_t> &vchRet) const {
        return GetOp2(pc, opcodeRet, &vchRet);
    }

    bool GetOp(const_iterator &pc, opcodetype &opcodeRet) const {
        return GetOp2(pc, opcodeRet, nullptr);
    }

    bool GetOp2(const_iterator &pc, opcodetype &opcodeRet,
                std::vector<uint8_t> *pvchRet) const {
        opcodeRet = OP_INVALIDOPCODE;
        if (pvchRet) pvchRet->clear();
        if (pc >= end()) return false;

        // Read instruction
        if (end() - pc < 1) return false;
        unsigned int opcode = *pc++;

        // Immediate operand
        if (opcode <= OP_PUSHDATA4) {
            unsigned int nSize = 0;
            if (opcode < OP_PUSHDATA1) {
                nSize = opcode;
            } else if (opcode == OP_PUSHDATA1) {
                if (end() - pc < 1) return false;
                nSize = *pc++;
            } else if (opcode == OP_PUSHDATA2) {
                if (end() - pc < 2) return false;
                nSize = ReadLE16(&pc[0]);
                pc += 2;
            } else if (opcode == OP_PUSHDATA4) {
                if (end() - pc < 4) return false;
                nSize = ReadLE32(&pc[0]);
                pc += 4;
            }
            if (end() - pc < 0 || (unsigned int)(end() - pc) < nSize)
                return false;
            if (pvchRet) pvchRet->assign(pc, pc + nSize);
            pc += nSize;
        }

        opcodeRet = (opcodetype)opcode;
        return true;
    }

    /** Encode/decode small integers: */
    static int DecodeOP_N(opcodetype opcode) {
        if (opcode == OP_0) return 0;
        assert(opcode >= OP_1 && opcode <= OP_16);
        return (int)opcode - (int)(OP_1 - 1);
    }
    static opcodetype EncodeOP_N(int n) {
        assert(n >= 0 && n <= 16);
        if (n == 0) return OP_0;
        return (opcodetype)(OP_1 + n - 1);
    }

    int FindAndDelete(const CScript &b) {
        int nFound = 0;
        if (b.empty()) return nFound;
        CScript result;
        iterator pc = begin(), pc2 = begin();
        opcodetype opcode;
        do {
            result.insert(result.end(), pc2, pc);
            while (static_cast<size_t>(end() - pc) >= b.size() &&
                   std::equal(b.begin(), b.end(), pc)) {
                pc = pc + b.size();
                ++nFound;
            }
            pc2 = pc;
        } while (GetOp(pc, opcode));

        if (nFound > 0) {
            result.insert(result.end(), pc2, end());
            *this = result;
        }

        return nFound;
    }
    int Find(opcodetype op) const {
        int nFound = 0;
        opcodetype opcode;
        for (const_iterator pc = begin(); pc != end() && GetOp(pc, opcode);)
            if (opcode == op) ++nFound;
        return nFound;
    }

    /**
     * Pre-version-0.6, Bitcoin always counted CHECKMULTISIGs as 20 sigops. With
     * pay-to-script-hash, that changed: CHECKMULTISIGs serialized in scriptSigs
     * are counted more accurately, assuming they are of the form
     *  ... OP_N CHECKMULTISIG ...
     *
     * After Genesis all sigops are counted accuratelly no matter how the flag is 
     * set. More than 16 pub keys are supported, but the size of the number representing
     * number of public keys must not be bigger than CScriptNum::MAXIMUM_ELEMENT_SIZE bytes.
     * If the size is bigger than that, or if the number of public keys is negative,
     * sigOpCountError is set to true,
     */
    uint64_t GetSigOpCount(bool fAccurate, bool isGenesisEnabled, bool& sigOpCountError) const;

    /**
     * Accurately count sigOps, including sigOps in pay-to-script-hash
     * transactions:
     */
    uint64_t GetSigOpCount(const CScript &scriptSig, bool isGenesisEnabled, bool& sigOpCountError) const;

    bool IsPayToScriptHash() const;
    bool IsWitnessProgram(int &version, std::vector<uint8_t> &program) const;

    /** Called by IsStandardTx and P2SH/BIP62 VerifyScript (which makes it
     * consensus-critical). */
    bool IsPushOnly(const_iterator pc) const;
    bool IsPushOnly() const;

    /**
     * Returns whether the script is guaranteed to fail at execution, regardless
     * of the initial stack. This allows outputs to be pruned instantly when
     * entering the UTXO set.
     * nHeight reflects the height of the block that script was mined in
     * For Genesis OP_RETURN this can return false negatives. For example if we have:
     *   <some complex script that always return OP_FALSE> OP_RETURN
     * this function will return false even though the ouput is unspendable.
     * 
     */

    bool IsUnspendable(bool isGenesisEnabled) const {
        if (isGenesisEnabled)
        {
            // Genesis restored OP_RETURN functionality. It no longer uncoditionally fails execution
            // The top stack value determines if execution suceeds, and OP_RETURN lock script might be spendable if 
            // unlock script pushes non 0 value to the stack.

            // We currently only detect OP_FALSE OP_RETURN as provably unspendable.
            return  (size() > 1 && *begin() == OP_FALSE && *(begin() + 1) == OP_RETURN);
        }
        else
        {
            return (size() > 0 && *begin() == OP_RETURN) ||
                (size() > 1 && *begin() == OP_FALSE && *(begin() + 1) == OP_RETURN) ||
                (size() > MAX_SCRIPT_SIZE_BEFORE_GENESIS);
        }
    }

    /**
     * Returns whether the script looks like a known OP_RETURN script. This is similar to IsUnspendable()
     * but it does not require nHeight. 
     * Use cases:
     *   - decoding transactions to avoid parsing OP_RETURN as other data
     *   - used in wallet for:
     *   -   for extracting addresses (we do not now how to do that for OP_RETURN) 
     *   -   logging unsolvable transactions that contain OP_RETURN
     */
    bool IsKnownOpReturn() const
    {
        return (size() > 0 && *begin() == OP_RETURN) ||
            (size() > 1 && *begin() == OP_FALSE && *(begin() + 1) == OP_RETURN);        
    }

    void clear() {
        // The default std::vector::clear() does not release memory.
        CScriptBase().swap(*this);
    }
};

std::ostream &operator<<(std::ostream &, const CScript &);
std::string to_string(const CScript&);

struct CScriptWitness {
    // Note that this encodes the data elements being pushed, rather than
    // encoding them as a CScript that pushes them.
    std::vector<std::vector<uint8_t>> stack;

    // Some compilers complain without a default constructor
    CScriptWitness() {}

    bool IsNull() const { return stack.empty(); }

    void SetNull() {
        stack.clear();
        stack.shrink_to_fit();
    }

    std::string ToString() const;
};

class CReserveScript {
public:
    CScript reserveScript;
    virtual void KeepScript() {}
    CReserveScript() {}
    virtual ~CReserveScript() {}
};

#endif // BITCOIN_SCRIPT_SCRIPT_H
