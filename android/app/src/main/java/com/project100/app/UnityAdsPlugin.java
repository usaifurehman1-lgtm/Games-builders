package com.project100.app;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.unity3d.ads.UnityAds;

@CapacitorPlugin(name = "UnityAds")
public class UnityAdsPlugin extends Plugin {

    @PluginMethod
    public void initialize(PluginCall call) {
        String gameId = call.getString("gameId", "");

        if (gameId.isEmpty()) {
            call.reject("Unity Game ID is required");
            return;
        }

        UnityAds.initialize(
            getActivity(),
            gameId,
            false,
            new UnityAds.IUnityAdsInitializationListener() {
                @Override
                public void onInitializationComplete() {
                    call.resolve();
                }

                @Override
                public void onInitializationFailed(
                    UnityAds.UnityAdsInitializationError error,
                    String message
                ) {
                    call.reject(message);
                }
            }
        );
    }

    @PluginMethod
    public void showRewarded(PluginCall call) {
        String placementId = call.getString("placementId", "");

        if (placementId.isEmpty()) {
            call.reject("Unity Placement ID is required");
            return;
        }

        UnityAds.show(
            getActivity(),
            placementId,
            new UnityAds.IUnityAdsShowListener() {
                @Override
                public void onUnityAdsShowFailure(
                    String placementId,
                    UnityAds.UnityAdsShowError error,
                    String message
                ) {
                    call.reject(message);
                }

                @Override
                public void onUnityAdsShowStart(String placementId) {}

                @Override
                public void onUnityAdsShowClick(String placementId) {}

                @Override
                public void onUnityAdsShowComplete(
                    String placementId,
                    UnityAds.UnityAdsShowCompletionState state
                ) {
                    if (state ==
                        UnityAds.UnityAdsShowCompletionState.COMPLETED) {
                        call.resolve();
                    } else {
                        call.reject("Rewarded video was not completed");
                    }
                }
            }
        );
    }
}
