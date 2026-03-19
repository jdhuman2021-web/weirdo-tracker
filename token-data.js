// Updated Token Data - 28 Tokens with Live Data
const TOKENS = [
    { symbol: 'PUNCH', name: 'パンチ', address: 'NV2RYH954cTJ3ckFUpvfqaQXU4ARqqDH3562nFSpump', price: 0.01483, change24h: 21.18, change1h: 0.94, liquidity: 743000 },
    { symbol: 'Jellybean', name: 'Jellybean', address: '412zDygnwP9DzitnQVgRKUFFTDmrYScFch6P2k39pump', price: 0.0006677, change24h: 0.96, change1h: -9.41, liquidity: 118000 },
    { symbol: 'Devious', name: 'Devious MF', address: 'CeoReCwAmt8iqjQoKQGEMqKERDWGxxDUED9zVYg3pump', price: 0.00008203, change24h: 6.29, change1h: 14.63, liquidity: 25000 },
    { symbol: 'HODL', name: 'HODL', address: 'Hh3oTaqDCKKfdBgsQEvxp9sUwyNf8x9qmKqE8x9pump', price: 0.00213, change24h: 15.63, change1h: 3.12, liquidity: 191000 },
    { symbol: 'JUICE', name: 'JUICE', address: '2LzLh5pHg3nDQz6goTLAvDXfDbSBgAR8qem3bdXdpump', price: 0.001783, change24h: -0.36, change1h: -1.58, liquidity: 154000 },
    { symbol: 'PIZZA', name: 'Bitcoin Pizza', address: 'G9ivB7K41a4G8m1k4QdxxN4L5eGKL7Mr12S26B85pump', price: 0.0002533, change24h: 5.87, change1h: 9.56, liquidity: 56000 },
    { symbol: 'BULK', name: 'bulk', address: 'F4TJfiMVi7zFGRJj4FVC1Zuj7fdCo6skKa4SnAU4pump', price: 0.000214, change24h: -17.14, change1h: 0.97, liquidity: 42000 },
    { symbol: 'Momo-chan', name: 'モモちゃん', address: '3zomtMhRRsBpLZeJLS86fgueXE7xAhoN8dnymNh8pump', price: 0.0002385, change24h: 19.74, change1h: -5.21, liquidity: 47000 },
    { symbol: 'NEW', name: 'New Token', address: '9S8edqWxoWz5LYLnxWUmWBJnePg35WfdYQp7HQkUpump', price: 0, change24h: 0, change1h: 0, liquidity: 0 },
    { symbol: 'MAX', name: 'maxxing', address: '32CdQdBUxbCsLy5AUHWmyidfwhgGUr9N573NBUrDpump', price: 0.002135, change24h: 1.96, change1h: 4.3, liquidity: 199000 },
    { symbol: 'GOYIM', name: 'Goyim', address: 'EJzqpRPxgZZVoVVuCXuQBNXp7mQzeH6FENMfuLRbpump', price: 0.0004182, change24h: -6.87, change1h: 0, liquidity: 103000 },
    { symbol: 'ARTEMIS', name: 'Artemis Moon Mission', address: 'AtdqW9HYpx6bzuXAyuVRz6a3UiTHLoNTRJDN8buXHem7', price: 0.0001273, change24h: -1.25, change1h: 0, liquidity: 32000 },
    { symbol: 'INU', name: 'INU', address: 'CmgJ1PobhUqB7MEa8qDkiG2TUpMTskWj8d9JeZWSpump', price: 0.00005544, change24h: -16.27, change1h: 0, liquidity: 22000 },
    { symbol: 'FISH', name: 'rainbowfish', address: 'AbeDBXvqGnmcvX8NtQg5qgREFTw7HynkCc4u97xcpump', price: 0.0001402, change24h: -9.75, change1h: 0, liquidity: 56000 },
    { symbol: 'BLIND', name: 'Blindfold Finance', address: 'BANKJmvhT8tiJRsBSS1n2HryMBPvT5Ze4HU95DUAmeta', price: 0.00004027, change24h: -2.14, change1h: 0, liquidity: 22000 },
    { symbol: 'AVICI', name: 'Avici', address: 'DP4omjjY94NRJrECHBZyUQSpGrjtukoDyUbqb9Zzpump', price: 0.7186, change24h: -6.67, change1h: 0, liquidity: 588000 },
    { symbol: 'REGRET', name: 'Regret', address: 'Cm6fNnMk7NfzStP9CZpsQA2v3jjzbcYGAxdJySmHpump', price: 0.00002733, change24h: -2.88, change1h: 0, liquidity: 19000 },
    { symbol: 'BUTT', name: 'Buttcoin', address: 'GB8KtQfMChhYrCYtd5PoAB42kAdkHnuyAincSSmFpump', price: 0.01179, change24h: -8.07, change1h: 0, liquidity: 572000 },
    { symbol: 'PIGEON', name: 'Pigeon Doctor', address: 'JB2wezZLdzWfnaCfHxLg193RS3Rh51ThiXxEDWQDpump', price: 0.0002668, change24h: 12.18, change1h: 0, liquidity: 83000 },
    { symbol: 'LABUBU', name: 'LABUBU', address: '2pjcq9k2X5oSArNKiVeQ2ENB63eJt8pwCabciGQGpump', price: 0.001195, change24h: 14.58, change1h: 0, liquidity: 403000 },
    { symbol: 'OPTIMISTIC', name: 'Optimistic Minion', address: 'J8PSdNP3QewKq2Z1JJJFDMaqF7KcaiJhR7gbr5KZpump', price: 0.0005342, change24h: 13.44, change1h: 0, liquidity: 63000 },
    { symbol: 'TRIPLET', name: 'Tung Tung Tung Sahur', address: 'A8C3xuqscfmyLrte3VmTqrAq8kgMASius9AFNANwpump', price: 0.002411, change24h: -5.29, change1h: 0, liquidity: 182000 },
    { symbol: 'FWOG', name: 'FWOG', address: '5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC', price: 0.005752, change24h: -2.66, change1h: 0, liquidity: 1440000 },
    { symbol: 'PONKE', name: 'PONKE', address: '5UUH9RTDiSpq6HKS6bp4NdU9PNJpXRXuiw6ShBTBhgH2', price: 0.03136, change24h: 1.01, change1h: 0, liquidity: 1560000 },
    { symbol: 'TROLL', name: 'TROLL', address: 'DQnkBM4eYYMnVE8Qy2K3BB7uts1fh2EwBVktEz6jpump', price: 0.0136, change24h: -2.82, change1h: 0, liquidity: 1292000 },
    { symbol: 'DOWGE', name: 'DOWGE', address: '9QSjVAg5rDfBZPhvKwZcB63St3r6bqohP3Adurkjpump', price: 0.004224, change24h: -4.07, change1h: 0, liquidity: 281000 },
    { symbol: 'ROSIE', name: 'Rosie', address: 'AVF9F4C4j8b1Kh4BmNHqybDaHgnZpJ7W7yLvL7hUpump', price: 0.000971, change24h: 2.34, change1h: 0, liquidity: 110000 },
    { symbol: 'LOBSTAR', name: 'Lobstar', address: '4TyZGqRLG3VcHTGMcLBoPUmqYitMVojXinAmkL8xpump', price: 0.006922, change24h: 23.03, change1h: 0, liquidity: 457000 },
    { symbol: 'TESTICLE', name: 'testicle', address: 'Gbu7JAKhTVtGyRryg8cYPiKNhonXpUqbrZuCDjfUpump', price: 0.006787, change24h: 14.25, change1h: 0, liquidity: 507000 },
    { symbol: 'SNOWBALL', name: 'snowball', address: 'AbeDBXvqGnmcvX8NtQg5qgREFTw7HynkCc4u97xcpump', price: 0.0002819, change24h: -9.06, change1h: 0, liquidity: 98000 }
];

// Export for use in main script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TOKENS };
}