ठीक है। मैं आपकी start_io_longin फ़ाइल के Cordova कोड को Capacitor के Java प्लगइन में बदलकर दे रहा हूँ, ताकि इसका ढाँचा आपकी Facebook और Unity Java फ़ाइलों जैसा हो।
फ़ाइल का नाम रखें: StartIoRewardedPlugin.java
package com.mygame.app;

import android.app.Activity;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import com.startapp.sdk.adsbase.StartAppAd;
import com.startapp.sdk.adsbase.VideoListener;
import com.startapp.sdk.adsbase.adlisteners.AdEventListener;
import com.startapp.sdk.adsbase.Ad;
import com.startapp.sdk.adsbase.adlisteners.AdDisplayListener;
import com.startapp.sdk.adsbase.StartAppAd.AdMode;

@CapacitorPlugin(name = "StartIoRewarded")
public class StartIoRewardedPlugin extends Plugin {

    private StartAppAd rewardedAd;

    @PluginMethod
    public void showRewarded(PluginCall call) {
        Activity activity = getActivity();

        if (activity == null) {
            call.reject("Android activity is unavailable");
            return;
        }

        activity.runOnUiThread(() -> {
            rewardedAd = new StartAppAd(activity);

            rewardedAd.setVideoListener(() -> {
                call.resolve();
            });

            rewardedAd.loadAd(
                AdMode.REWARDED_VIDEO,
                new AdEventListener() {
                    @Override
                    public void onReceiveAd(Ad ad) {
                        rewardedAd.showAd();
                    }

                    @Override
                    public void onFailedToReceiveAd(Ad ad) {
                        call.reject("Start.io rewarded video failed to load");
                    }
                }
            );
        });
    }
}
ध्यान दें: यह कोड Java प्लगइन का प्रारूप देता है, लेकिन इसे अभी तैयार और टेस्ट किया हुआ न मानें। Start.io SDK के आपके प्रोजेक्ट में इस्तेमाल हो रहे संस्करण के अनुसार VideoListener और AdMode के imports या callbacks बदल सकते हैं। इसे चलाने के लिए Start.io Android SDK dependency भी आवश्यक है।
