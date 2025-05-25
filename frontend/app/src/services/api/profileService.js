/**
 * Profile Service for GlobalCoyn
 * Handles user profile management with IPFS integration
 */

import axios from 'axios';
import ipfsService from './ipfsService';

// Production or dev API URLs
const PROD_API_URL = 'https://globalcoyn.com/api';
const DEV_API_URL = 'http://localhost:8001/api';

// Environment detection
// 1. Check for explicit environment setting in localStorage (useful for testing)
// 2. Check for REACT_APP_ENV environment variable
// 3. Check domain name
const ENV_OVERRIDE = localStorage.getItem('gcn_environment');
const isProduction = ENV_OVERRIDE === 'production' || 
                    process.env.REACT_APP_ENV === 'production' || 
                    window.location.hostname === 'globalcoyn.com';

// Logging environment
console.log('GlobalCoyn API Environment:', isProduction ? 'PRODUCTION' : 'DEVELOPMENT');

class ProfileService {
  constructor() {
    this.apiUrl = isProduction ? PROD_API_URL : DEV_API_URL;
    this.cache = new Map(); // Local profile cache
  }

  /**
   * Create or update user profile
   * @param {string} walletAddress - Wallet address
   * @param {string} alias - User alias
   * @param {string} bio - User bio
   * @param {string} ipfsHash - IPFS hash of profile image
   * @returns {Promise<Object>} Operation result
   */
  async setProfile(walletAddress, alias, bio = '', ipfsHash = '') {
    try {
      const response = await fetch(`${this.apiUrl}/profiles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          walletAddress,
          alias,
          bio,
          ipfsHash
        })
      });

      const result = await response.json();

      if (result.success) {
        // Cache the profile locally
        this.cache.set(walletAddress, result.profile);
        
        // Add image URL for convenience
        if (result.profile.ipfsHash) {
          result.profile.imageUrl = ipfsService.getImageUrl(result.profile.ipfsHash);
        }
      }

      return result;

    } catch (error) {
      console.error('Set profile error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get user profile by wallet address
   * @param {string} walletAddress - Wallet address
   * @param {boolean} useCache - Whether to use local cache
   * @returns {Promise<Object>} User profile result
   */
  async getProfile(walletAddress, useCache = true) {
    try {
      // Check cache first
      if (useCache && this.cache.has(walletAddress)) {
        return {
          success: true,
          profile: this.cache.get(walletAddress)
        };
      }

      const response = await fetch(`${this.apiUrl}/profiles/${walletAddress}`);
      const result = await response.json();

      if (result.success && result.profile) {
        // Add image URL and cache
        if (result.profile.ipfsHash) {
          result.profile.imageUrl = await ipfsService.getImageUrlWithFallback(result.profile.ipfsHash);
        }
        this.cache.set(walletAddress, result.profile);
      }

      return result;

    } catch (error) {
      console.error('Get profile error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check if alias is available
   * @param {string} alias - Alias to check
   * @returns {Promise<boolean>} Whether alias is available
   */
  async isAliasAvailable(alias) {
    try {
      const response = await fetch(`${this.apiUrl}/profiles/alias/${alias}/available`);
      const result = await response.json();
      return result.available;
    } catch (error) {
      console.error('Check alias availability error:', error);
      return false;
    }
  }

  /**
   * Search profiles
   * @param {string} query - Search query
   * @param {number} limit - Result limit
   * @returns {Promise<Array>} Search results
   */
  async searchProfiles(query, limit = 10) {
    try {
      const response = await fetch(`${this.apiUrl}/profiles/search/${encodeURIComponent(query)}?limit=${limit}`);
      const result = await response.json();

      if (result.success && result.results) {
        // Add image URLs
        for (const profile of result.results) {
          if (profile.ipfsHash) {
            profile.imageUrl = ipfsService.getImageUrl(profile.ipfsHash);
          }
        }
        return result.results;
      }

      return [];

    } catch (error) {
      console.error('Search profiles error:', error);
      return [];
    }
  }

  /**
   * Update profile image only
   * @param {string} walletAddress - Wallet address
   * @param {File} imageFile - New profile image
   * @returns {Promise<Object>} Operation result
   */
  async updateProfileImage(walletAddress, imageFile) {
    try {
      // Upload new image to IPFS
      const uploadResult = await ipfsService.uploadImage(imageFile);

      if (!uploadResult.success) {
        throw new Error(`Image upload failed: ${uploadResult.error}`);
      }

      // Get current profile
      const currentProfile = await this.getProfile(walletAddress);
      if (!currentProfile.success || !currentProfile.profile) {
        throw new Error('Profile not found');
      }

      // Update profile with new image
      return await this.setProfile(
        walletAddress,
        currentProfile.profile.alias,
        currentProfile.profile.bio,
        uploadResult.hash
      );

    } catch (error) {
      console.error('Update profile image error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get default avatar URL
   * @param {string} walletAddress - Wallet address for generating unique avatar
   * @returns {string} Default avatar URL
   */
  getDefaultAvatar(walletAddress) {
    // Generate deterministic avatar based on wallet address
    const seed = walletAddress || 'default';
    return `https://api.dicebear.com/7.x/identicon/svg?seed=${seed}&backgroundColor=dbeafe`;
  }

  /**
   * Clear profile cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Delete profile
   * @param {string} walletAddress - Wallet address
   * @returns {Promise<Object>} Operation result
   */
  async deleteProfile(walletAddress) {
    try {
      const response = await fetch(`${this.apiUrl}/profiles/${walletAddress}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (result.success) {
        // Remove from cache
        this.cache.delete(walletAddress);
      }

      return result;

    } catch (error) {
      console.error('Delete profile error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default new ProfileService();