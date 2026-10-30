package dev.beampro.settings;

import android.content.Context;
import android.util.AtomicFile;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/** Optional SBS startup for models whose original home configuration is mono. */
public final class ExperimentalStereo {
    private static final String FILE = "unbound-experimental-stereo";
    public static final int ORIGINAL = 0, FORCE_3D = 1, FORCE_2D = 2;
    private ExperimentalStereo() {}

    private static AtomicFile file(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), FILE));
    }
    public static int mode(Context context) {
        try {
            byte[] value = file(context).readFully();
            // Retired 2D 60 Hz choices also retain the original model defaults.
            return value.length == 1 && value[0] >= 0 && value[0] <= FORCE_2D ? value[0] : ORIGINAL;
        } catch (Exception absent) { return ORIGINAL; }
    }
    public static boolean enabled(Context context) { return mode(context) == FORCE_3D; }
    /** Keep glasses whose original configuration is stereo in their current 2D mode. */
    public static boolean monoEnabled(Context context) { return mode(context) == FORCE_2D; }
    public static void save(Context context, boolean enabled) throws Exception {
        save(context, enabled ? FORCE_3D : ORIGINAL);
    }
    public static void save(Context context, int mode) throws Exception {
        // Unity's audited native reader uses this package-owned path. Refuse a
        // profile in which Java and the renderer would read different files.
        if (context.getPackageName().equals("dev.markpronkin.unbound")
                && !context.getFilesDir().getCanonicalFile().equals(
                        new File("/data/user/0/dev.markpronkin.unbound/files").getCanonicalFile()))
            throw new IllegalStateException("Display overrides are unavailable in this Android user profile.");
        AtomicFile file = file(context);
        FileOutputStream stream = file.startWrite();
        try { stream.write(mode); file.finishWrite(stream); }
        catch (Exception failure) { file.failWrite(stream); throw failure; }
    }
    private static Object field(Object owner, String name) throws Exception {
        for (Class<?> type = owner.getClass(); type != null; type = type.getSuperclass()) {
            try { Field f = type.getDeclaredField(name); f.setAccessible(true); return f.get(owner); }
            catch (NoSuchFieldException absent) {}
        }
        throw new NoSuchFieldException(name);
    }
    private static boolean stereo(int value, boolean ethernet) {
        return ethernet ? value >= 5 && value <= 8 : value == 2 || value == 3 || value == 4 || value == 9;
    }
    /** The SDK has separate legacy EGlassMode and Ethernet EDID namespaces. */
    public static int selectConfig(int original, Object manager) {
        try {
            Context context = (Context) field(manager, "mContext");
            int mode = mode(context);
            if (mode == ORIGINAL) return original;
            Object control = field(manager, "mNRServiceControl");
            boolean ethernet = Boolean.TRUE.equals(field(control, "isEthernetSeries"));
            if (mode == FORCE_2D) {
                // Glasses that refuse the 3D EDID switch show one cropped half per
                // eye. Stay in the mode the glasses currently report instead.
                if (!stereo(original, ethernet)) return original;
                Method read = control.getClass().getMethod("get2D3D");
                read.setAccessible(true);
                int current = ((Number) read.invoke(control)).intValue();
                return stereo(current, ethernet) ? original : current;
            }
            boolean mono = ethernet ? original >= 1 && original <= 4
                    : original == 1 || original == 5 || original == 10 || original == 11;
            return mono ? (ethernet ? 5 : 3) : original;
        } catch (Exception failure) {
            Log.w("UnboundStereo", "Keeping original glasses configuration", failure);
            return original;
        }
    }
}
