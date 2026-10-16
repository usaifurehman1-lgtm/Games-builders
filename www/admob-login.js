import { AdMob } from '@capacitor-community/admob';

export async function initializeAdMob() {
  await AdMob.initialize();
}

export async function showAdMobRewardedVideo(adId) {
  if (!adId) throw new Error('AdMob rewarded ad unit ID is required');

  await AdMob.prepareRewardVideoAd({
    adId,
    isTesting: true
  });

  return await AdMob.showRewardVideoAd();
}
