// General helper functions

export const formatCurrency = (amount, decimals = 6) => {
  return parseFloat(amount).toFixed(decimals);
};

export const formatHash = (hash, length = 8) => {
  if (!hash) return '';
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
};

export const formatTimestamp = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString();
};

export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return false;
  }
};