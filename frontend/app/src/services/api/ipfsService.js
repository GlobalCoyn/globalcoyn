/**
 * IPFS Service for GlobalCoyn Profile System
 * Handles image uploads and retrieval from IPFS via backend API
 */

class IPFSService {
  constructor() {
    this.apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    this.ipfsGateway = 'https://gateway.pinata.cloud/ipfs/';
    
    // Fallback gateways if primary fails
    this.fallbackGateways = [
      'https://ipfs.io/ipfs/',
      'https://cloudflare-ipfs.com/ipfs/',
      'https://gateway.ipfs.io/ipfs/'
    ];
  }

  /**
   * Upload image to IPFS via backend API
   * @param {File} file - Image file to upload
   * @param {Object} metadata - Optional metadata for the file
   * @returns {Promise<Object>} Upload result with IPFS hash
   */
  async uploadImage(file, metadata = {}) {
    try {
      // Validate file
      const validation = await this.validateImageFile(file);
      if (!validation.valid) {
        throw new Error(validation.error);
      }

      // Compress image if needed
      const compressedFile = await this.compressImage(file);
      
      // Convert file to base64
      const base64Data = await this.fileToBase64(compressedFile);

      // Upload via backend API
      const response = await fetch(`${this.apiBaseUrl}/profiles/ipfs/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageData: base64Data,
          fileName: file.name,
          metadata
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Upload failed');
      }

      return {
        success: true,
        hash: result.hash,
        url: result.url
      };

    } catch (error) {
      console.error('IPFS upload error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Convert file to base64
   * @param {File} file - File to convert
   * @returns {Promise<string>} Base64 string
   */
  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Get image URL from IPFS hash
   * @param {string} ipfsHash - IPFS hash of the image
   * @returns {string} Full URL to access the image
   */
  getImageUrl(ipfsHash) {
    if (!ipfsHash) return null;
    return `${this.ipfsGateway}${ipfsHash}`;
  }

  /**
   * Get image with fallback gateways
   * @param {string} ipfsHash - IPFS hash of the image
   * @returns {Promise<string>} Working image URL
   */
  async getImageUrlWithFallback(ipfsHash) {
    if (!ipfsHash) return null;

    // Try primary gateway first
    const primaryUrl = this.getImageUrl(ipfsHash);
    if (await this.checkImageExists(primaryUrl)) {
      return primaryUrl;
    }

    // Try fallback gateways
    for (const gateway of this.fallbackGateways) {
      const url = `${gateway}${ipfsHash}`;
      if (await this.checkImageExists(url)) {
        return url;
      }
    }

    return primaryUrl; // Return primary as last resort
  }

  /**
   * Check if image exists at URL
   * @param {string} url - Image URL to check
   * @returns {Promise<boolean>} Whether image exists
   */
  async checkImageExists(url) {
    try {
      const response = await fetch(url, { 
        method: 'HEAD',
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Validate image file before upload
   * @param {File} file - File to validate
   * @returns {Promise<Object>} Validation result
   */
  async validateImageFile(file) {
    // Check file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Please use JPEG, PNG, GIF, or WebP.'
      };
    }

    // Check file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File too large. Maximum size is 5MB.'
      };
    }

    // Check dimensions
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const maxDimension = 1024;
        if (img.width > maxDimension || img.height > maxDimension) {
          resolve({
            valid: false,
            error: `Image too large. Maximum dimensions are ${maxDimension}x${maxDimension}px.`
          });
        } else {
          resolve({ valid: true });
        }
      };
      img.onerror = () => {
        resolve({
          valid: false,
          error: 'Invalid image file.'
        });
      };
      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * Compress image before upload
   * @param {File} file - Image file to compress
   * @param {number} quality - Compression quality (0-1)
   * @returns {Promise<File>} Compressed image file
   */
  async compressImage(file, quality = 0.8) {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions (max 512x512 for profile images)
        const maxSize = 512;
        let { width, height } = img;

        if (width > height) {
          if (width > maxSize) {
            height = (height * maxSize) / width;
            width = maxSize;
          }
        } else {
          if (height > maxSize) {
            width = (width * maxSize) / height;
            height = maxSize;
          }
        }

        canvas.width = width;
        canvas.height = height;

        // Draw and compress
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => {
          const compressedFile = new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
          });
          resolve(compressedFile);
        }, 'image/jpeg', quality);
      };

      img.src = URL.createObjectURL(file);
    });
  }
}

export default new IPFSService();