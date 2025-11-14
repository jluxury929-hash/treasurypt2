// PRODUCTION TREASURY - SENDS REAL ETH
const express = require('express');
const { ethers } = require('ethers');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const TREASURY_PRIVATE_KEY = process.env.TREASURY_PRIVATE_KEY;
const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY;
const PORT = process.env.PORT || 3000;

const provider = new ethers.providers.AlchemyProvider('homestead', ALCHEMY_API_KEY);
const treasuryWallet = new ethers.Wallet(TREASURY_PRIVATE_KEY, provider);

console.log(` Treasury: ${treasuryWallet.address}`);

app.get('/', async (req, res) => {
  const balance = await provider.getBalance(treasuryWallet.address);
  const balanceETH = ethers.utils.formatEther(balance);
  
  res.json({
    status: 'online',
    treasury_address: treasuryWallet.address,
    treasury_eth_balance: parseFloat(balanceETH),
    network: 'Ethereum Mainnet',
    chain_id: 1,
    block_number: await provider.getBlockNumber()
  });
});

app.post('/api/claim/earnings', async (req, res) => {
  const { userWallet, amountETH, amountUSD, backupId } = req.body;

  console.log(` Withdrawal: ${amountETH} ETH to ${userWallet}`);

  try {
    if (!ethers.utils.isAddress(userWallet)) {
      throw new Error('Invalid address');
    }

    if (!amountETH || amountETH <= 0 || amountETH > 10) {
      throw new Error('Invalid amount');
    }

    const treasuryBalance = await provider.getBalance(treasuryWallet.address);
    const treasuryBalanceETH = parseFloat(ethers.utils.formatEther(treasuryBalance));
    
    if (treasuryBalanceETH < amountETH + 0.001) {
      throw new Error(`Low treasury: ${treasuryBalanceETH.toFixed(6)} ETH`);
    }

    const amountWei = ethers.utils.parseEther(amountETH.toString());
    
    const tx = await treasuryWallet.sendTransaction({
      to: userWallet,
      value: amountWei
    });

    console.log(` TX: ${tx.hash}`);

    const receipt = await tx.wait();

    console.log(` Confirmed! Block ${receipt.blockNumber}`);

    res.json({
      success: true,
      txHash: tx.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString(),
      amount: amountETH,
      amountUSD: amountUSD,
      recipientWallet: userWallet,
      etherscanUrl: `https://etherscan.io/tx/${tx.hash}`
    });

  } catch (error) {
    console.error(` Failed: ${error.message}`);
    res.status(400).json({ success: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(` Treasury running on ${PORT}`);
});
