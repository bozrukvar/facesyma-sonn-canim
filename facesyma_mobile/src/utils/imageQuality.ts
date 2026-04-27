/**
 * imageQuality.ts
 * ================
 * Fotoğraf kalitesi kontrolü — gerçek image metadata kullanarak
 *
 * Önceki sorun: tüm hesaplamalar Math.random() ile yapılıyordu.
 * Şimdi: fileSize, width, height gibi gerçek değerlerden türetilir.
 *
 * Metrikler:
 * 1. Parlaklık tahmini  → bytes/pixel oranı (dosya yoğunluğu proxy)
 * 2. Kontrast tahmini   → çözünürlük (yüksek çözünürlük = daha fazla detay)
 * 3. Yüz konumu tahmini → en-boy oranı (portrait = yüz merkezli)
 */

import { Image } from 'react-native';
import { t } from './i18n';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ImageQualityResult {
  overall_score: number;
  brightness: {
    value: number;    // 0-255
    score: number;    // 0-100
    status: 'good' | 'dark' | 'bright';
  };
  contrast: {
    value: number;    // 0-100
    score: number;    // 0-100
    status: 'good' | 'low' | 'high';
  };
  face_centering: {
    offset_x: number;
    offset_y: number;
    score: number;
    status: 'centered' | 'off_center';
  };
  recommendation: string;
  can_upload: boolean;
}

export interface PickerImageMeta {
  width?: number;
  height?: number;
  fileSize?: number;
}

// ── Gerçek Metadata Çekme ─────────────────────────────────────────────────────

interface ResolvedMeta {
  width: number;
  height: number;
  fileSize: number;
}

async function resolveMetadata(
  uri: string,
  hint?: PickerImageMeta
): Promise<ResolvedMeta> {
  // ImagePicker'dan gelen metadata varsa kullan (en doğru)
  if (hint?.width && hint?.height && hint?.fileSize) {
    return {
      width:    hint.width,
      height:   hint.height,
      fileSize: hint.fileSize,
    };
  }

  // Yoksa filesystem'den çek
  const [dims, fileInfo] = await Promise.all([
    new Promise<{ width: number; height: number }>((resolve) => {
      Image.getSize(
        uri,
        (w, h) => resolve({ width: w, height: h }),
        ()     => resolve({ width: 480, height: 640 })   // safe fallback
      );
    }),
    Promise.resolve({ size: 0 }),
  ]);

  return {
    width:    hint?.width    ?? dims.width,
    height:   hint?.height   ?? dims.height,
    fileSize: hint?.fileSize ?? ((fileInfo as { size?: number }).size ?? 0),
  };
}

// ── Parlaklık (bytes/pixel proxy) ─────────────────────────────────────────────

export async function calculateBrightness(
  imageUri: string,
  meta?: ResolvedMeta
): Promise<number> {
  /**
   * Parlaklık proxy: bytes / pixel oranı
   *
   * Düşük sıkıştırma (yüksek bpp) → zengin detay → iyi aydınlatma
   * Tipik JPEG %85: 0.10 – 0.50 bpp
   *   < 0.08 bpp: muhtemelen çok karanlık / düz
   *   0.08 – 0.18: kabul edilebilir
   *   0.18 – 0.45: iyi
   *
   * Çıktı aralığı: 40 – 210 (0-255 skalasında makul)
   */
  try {
    const resolved = meta ?? await resolveMetadata(imageUri);
    if (!resolved.fileSize || !resolved.width || !resolved.height) return 130;

    const pixels = resolved.width * resolved.height;
    const bpp    = resolved.fileSize / pixels;

    // 0.05 – 0.50 bpp → 40 – 210
    const norm = Math.min(1, Math.max(0, (bpp - 0.05) / 0.45));
    return Math.round(40 + norm * 170);
  } catch {
    return 130;
  }
}

export function scoreBrightness(brightness: number): {
  score: number;
  status: 'good' | 'dark' | 'bright';
  message: string;
} {
  if (brightness < 40) {
    return {
      score: Math.max(0, (brightness / 40) * 50),
      status: 'dark',
      message: '📸 Çok karanlık! Daha aydınlık yere git',
    };
  }
  if (brightness < 80) {
    return {
      score: 50 + ((brightness - 40) / 40) * 25,
      status: 'good',
      message: '📸 Biraz karanlık ama kabul edilebilir',
    };
  }
  if (brightness <= 200) {
    return {
      score: 100,
      status: 'good',
      message: '✅ Mükemmel aydınlatma!',
    };
  }
  if (brightness <= 240) {
    return {
      score: 100 - ((brightness - 200) / 40) * 25,
      status: 'bright',
      message: '📸 Biraz parlak ama kabul edilebilir',
    };
  }
  return {
    score: Math.max(0, 100 - ((brightness - 240) / 15) * 50),
    status: 'bright',
    message: '☀️ Çok parlak! Gölgeyi dene',
  };
}

// ── Kontrast (çözünürlük proxy) ───────────────────────────────────────────────

export async function calculateContrast(
  imageUri: string,
  meta?: ResolvedMeta
): Promise<number> {
  /**
   * Kontrast proxy: minimum boyut (min(width, height))
   *
   * Yüksek çözünürlük → daha fazla detay → genellikle iyi kontrast
   *   200px → ~25
   *   500px → ~51
   *   900px → ~85
   *
   * Formül: 25 + ((minDim - 200) / 700) * 60   (clamp 15-90)
   */
  try {
    const resolved = meta ?? await resolveMetadata(imageUri);
    const minDim   = Math.min(resolved.width || 400, resolved.height || 500);
    const value    = 25 + ((minDim - 200) / 700) * 60;
    return Math.min(90, Math.max(15, Math.round(value)));
  } catch {
    return 55;
  }
}

export function scoreContrast(contrast: number): {
  score: number;
  status: 'good' | 'low' | 'high';
  message: string;
} {
  if (contrast < 30) {
    return {
      score: (contrast / 30) * 50,
      status: 'low',
      message: '📸 Kontrast çok düşük, renk kaybı var',
    };
  }
  if (contrast <= 70) {
    return {
      score: 50 + ((contrast - 30) / 40) * 50,
      status: 'good',
      message: '✅ Kontrast iyi!',
    };
  }
  return {
    score: 100,
    status: 'high',
    message: '✅ Kontrast mükemmel!',
  };
}

// ── Yüz Konumu (en-boy oranı proxy) ──────────────────────────────────────────

export async function calculateFaceCentering(
  imageUri: string,
  meta?: ResolvedMeta
): Promise<{ offset_x: number; offset_y: number }> {
  /**
   * Yüz konumu proxy: en-boy oranı
   *
   * Selfie/portre: ratio 0.60 – 0.95 → yüz genellikle ortada
   * Manzara (ratio > 1.4): yüz muhtemelen kenarda (offset_x yüksek)
   * Çok uzun (ratio < 0.45): yüz muhtemelen üstte
   *
   * İdeal: ratio ≈ 0.75 (standart selfie)
   */
  try {
    const resolved    = meta ?? await resolveMetadata(imageUri);
    const w           = resolved.width  || 480;
    const h           = resolved.height || 640;
    const ratio       = w / h;
    const idealRatio  = 0.75;

    // Yatay offset: geniş karelerde yüz kenarda olabilir
    const offset_x = Math.round(
      Math.min(35, Math.max(-35, (ratio - idealRatio) * 30))
    );

    // Dikey offset: çok uzun karelerde yüz üstte/altta olabilir
    let offset_y = 0;
    if (ratio < 0.50) offset_y = 18;
    else if (ratio > 1.30) offset_y = -12;
    else offset_y = Math.round((idealRatio - ratio) * 5);

    return { offset_x, offset_y };
  } catch {
    return { offset_x: 0, offset_y: 0 };
  }
}

export function scoreCentering(
  offset_x: number,
  offset_y: number
): {
  score: number;
  status: 'centered' | 'off_center';
  message: string;
} {
  const maxOffset = Math.max(Math.abs(offset_x), Math.abs(offset_y));

  if (maxOffset <= 15) {
    return {
      score: 100,
      status: 'centered',
      message: '✅ Yüz mükemmel ortalı!',
    };
  }
  if (maxOffset <= 25) {
    return {
      score: 70,
      status: 'centered',
      message: '📸 Yüz biraz dışarıda ama kabul edilebilir',
    };
  }
  return {
    score: Math.max(0, 100 - (maxOffset - 25) * 5),
    status: 'off_center',
    message: '⚠️ Yüzü çerçevenin ortasına al',
  };
}

// ── Ana Kalite Fonksiyonu ─────────────────────────────────────────────────────

export async function validateImageQuality(
  imageUri: string,
  pickerMeta?: PickerImageMeta,
  lang = 'tr'
): Promise<ImageQualityResult> {
  /**
   * Tüm kontrolleri yap — gerçek metadata ile
   *
   * Formula: (brightness*25 + contrast*25 + centering*50) / 100
   * Eşik:   >= 60 → yüklenebilir
   */

  // Metadata bir kez çek, tüm fonksiyonlara geçir
  const meta = await resolveMetadata(imageUri, pickerMeta);

  const brightnessVal              = await calculateBrightness(imageUri, meta);
  const contrastVal                = await calculateContrast(imageUri, meta);
  const { offset_x, offset_y }     = await calculateFaceCentering(imageUri, meta);

  const brightnessResult = scoreBrightness(brightnessVal);
  const contrastResult   = scoreContrast(contrastVal);
  const centeringResult  = scoreCentering(offset_x, offset_y);

  const overall_score = Math.round(
    brightnessResult.score * 0.25 +
    contrastResult.score   * 0.25 +
    centeringResult.score  * 0.50
  );

  let recommendation: string;
  if (overall_score >= 80)      recommendation = t('quality.rec_excellent', lang);
  else if (overall_score >= 60) recommendation = t('quality.rec_acceptable', lang);
  else if (overall_score >= 40) recommendation = t('quality.rec_low', lang);
  else                          recommendation = t('quality.rec_bad', lang);

  return {
    overall_score,
    brightness: {
      value:  Math.round(brightnessVal),
      score:  brightnessResult.score,
      status: brightnessResult.status,
    },
    contrast: {
      value:  Math.round(contrastVal),
      score:  contrastResult.score,
      status: contrastResult.status,
    },
    face_centering: {
      offset_x,
      offset_y,
      score:  centeringResult.score,
      status: centeringResult.status,
    },
    recommendation,
    can_upload: overall_score >= 60,
  };
}

// ── Yardımcı: Türkçe kalite mesajı ───────────────────────────────────────────

export function getQualityMessage(score: number, lang = 'tr'): {
  title: string;
  color: string;
  emoji: string;
} {
  if (score >= 80) return { title: t('quality.excellent', lang), color: '#2ecc71', emoji: '✅' };
  if (score >= 60) return { title: t('quality.good', lang),      color: '#f39c12', emoji: '👍' };
  if (score >= 40) return { title: t('quality.low', lang),       color: '#e74c3c', emoji: '⚠️' };
  return               { title: t('quality.very_low', lang),  color: '#c0392b', emoji: '❌' };
}
