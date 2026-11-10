// Makes the Android app full screen (immersive): run after `npx cap add android`.
// The status bar and navigation bar are hidden; a swipe from the edge shows them
// for a moment, then they hide again. Capacitor's SystemBars plugin (configured
// in capacitor.config.json) handles the keyboard and the screen cutout insets.
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("../android/app/src/main/", import.meta.url).pathname;

function find(dir, name) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      const hit = find(full, name);
      if (hit) return hit;
    } else if (entry === name) return full;
  }
  return null;
}

const activity = find(join(root, "java"), "MainActivity.java");
if (!activity) throw new Error("MainActivity.java not found: run `npx cap add android` first");
const pkg = /^package\s+([\w.]+);/m.exec(readFileSync(activity, "utf8"))[1];

writeFileSync(activity, `package ${pkg};

import android.os.Build;
import android.os.Bundle;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

/** Claide IDE runs full screen: no status bar, no navigation bar. */
public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            WindowManager.LayoutParams params = getWindow().getAttributes();
            params.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            getWindow().setAttributes(params);
        }
        hideSystemBars();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            hideSystemBars();
        }
    }

    private void hideSystemBars() {
        WindowInsetsControllerCompat controller =
            WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        controller.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        controller.hide(WindowInsetsCompat.Type.systemBars());
    }
}
`);

const manifestPath = join(root, "AndroidManifest.xml");
let manifest = readFileSync(manifestPath, "utf8");
if (/android:windowSoftInputMode="[^"]*"/.test(manifest)) {
  manifest = manifest.replace(/android:windowSoftInputMode="[^"]*"/, 'android:windowSoftInputMode="adjustResize"');
} else {
  manifest = manifest.replace(/<activity\b/, '<activity\n            android:windowSoftInputMode="adjustResize"');
}
writeFileSync(manifestPath, manifest);
console.log(`Full screen enabled in ${activity}`);
