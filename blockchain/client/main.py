import uvicorn

from fastapi import FastAPI, Body, Depends, HTTPException,  File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from config import *
from pydantic import BaseModel
import json

# import data
from khanhSolana.khanhSolanaDataBase import *
from khanhSolana.khanhSolanaData import *
from khanhSolana.bs58 import bs58

app = FastAPI(title="Solana API",
              description="Solana API Management",
              version="v2.0",
              contact={
                  "name": "Khanh Master"
              })

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solana Client
client = KhanhSolanaClient(programId, False, "devnet")

# Solana instruction data
@BaseInstructionDataClass(name="init_voter")
class VoterInitInstruction:
    cccd_sha256=KhanhArrayStruct(32, lambda: KhanhUint8(0))

@BaseInstructionDataClass(name="init_candidate")
class CandidateInitInstruction:
    pass

@BaseInstructionDataClass(name="vote")
class VoteInstruction():
    pass

# Account data
@BaseStructClass
class VoterData:
    owner=KhanhHex(32)
    cccd_sha256=KhanhHex(32)
    vote_who=KhanhHex(32)
    voted=KhanhUint64(0)

@BaseStructClass
class CandidateData:
    # owner=KhanhHex(32)
    num_votes=KhanhUint64(0)

# Status
GlobalStaus = {
    "type_account": "voter",
}

# Router
@app.post("/convert-keypair-to-private-key")
async def convert_keypair_to_private_key(file: UploadFile):
    # Bytes to string
    result = file.file.read()
    keypair_json = json.loads(result)
    keypair_bytes = bytes(keypair_json)
    return {
        "public_key": bs58.encode(keypair_bytes[32:]),
        "private_key": bs58.encode(keypair_bytes),
    }

@app.post("/login-as-voter")
async def login_as_voter(secretKey: str):
    GlobalStaus["type_account"] = "voter"
    return client.make_key_pair(secretKey, "voter")

@app.post("/login-as-candidate")
async def login_as_candidate(secretKey: str):
    GlobalStaus["type_account"] = "candidate"
    return client.make_key_pair(secretKey, "candidate")

@app.post("/init-voter")
async def init_voter(secretKey: str, cccd: str):
    keypair = makeKeyPair(secretKey)
    public_key_seed = findProgramAddress(keypair.public_key, "voter", client.program_id)
    cccd_sha256 = KhanhHex(32)
    cccd_sha256.object2struct(hash256(cccd).hex())
    return client.send_transaction(
        VoterInitInstruction(cccd_sha256=cccd_sha256),
        [
            makeKeyPair(payerPrivateKey).public_key,
            keypair.public_key,
            makePublicKey(public_key_seed),
            makePublicKey("SysvarRent111111111111111111111111111111111"),
            makePublicKey("11111111111111111111111111111111"),
        ],
        [
            makeKeyPair(payerPrivateKey),
            keypair
        ]
    )

@app.post("/init-candidate")
async def init_candidate(secretKey: str):
    keypair = makeKeyPair(secretKey)
    public_key_seed = findProgramAddress(keypair.public_key, "candidate", client.program_id)
    return client.send_transaction(
        CandidateInitInstruction(),
        [
            makeKeyPair(payerPrivateKey).public_key,
            keypair.public_key,
            makePublicKey(public_key_seed),
            makePublicKey("SysvarRent111111111111111111111111111111111"),
            makePublicKey("11111111111111111111111111111111"),
        ],
        [
            makeKeyPair(payerPrivateKey),
            keypair
        ]
    )

@app.get("/get-account-info")
async def get_account_info():
    return client.get_account_info()

@app.get("/get-account-data")
async def get_account_data():
    if GlobalStaus["type_account"] == "voter":
        return client.get_account_data(VoterData)
    elif GlobalStaus["type_account"] == "candidate":
        return client.get_account_data(CandidateData)

@app.get("/get-balance")
async def get_balance():
    return client.get_balance()

@app.post("/airdrop")
async def airdrop(amount: int = 1):
    return client.drop_sol(amount)

@app.post("/send-vote")
async def send_vote(candidatePublicKey: str):
    try:
        client.get_account_info()
    except Exception as e:
        return {"error": str(e)}
    
    return client.send_transaction(
        VoteInstruction(),
        [
            makeKeyPair(payerPrivateKey).public_key,
            client.keypair.public_key,
            client.public_key_seed,
            makePublicKey(candidatePublicKey),
            makePublicKey("SysvarRent111111111111111111111111111111111"),
            makePublicKey("11111111111111111111111111111111"),
        ],
        [
            makeKeyPair(payerPrivateKey),
            client.keypair
        ]
    )

# Run
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=openPortAPI)
