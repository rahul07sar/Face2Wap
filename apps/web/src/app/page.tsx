/**
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        page.tsx
 * Module:      Web / Home
 * Description:
 *
 * Renders the Face2Wap upload landing page and introduces the image and video
 * face-swap workflow.
 *
 * ============================================================================
 */

import UploadClient from "./components/upload-client";
import styles from "./page.module.css";
import Image from "next/image";

export default function Home() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <a className={styles.brand} href="/" aria-label="Face2Wap home">
          <Image
            src="/face2wap_logo.png"
            alt="Face2Wap"
            width={180}
            height={60}
            priority
            className={styles.brandLogo}
          />
        </a>
        <nav className={styles.navigation} aria-label="Primary navigation">
          <a href="#upload">Create</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#about">About</a>
        </nav>
      </header>

      <main className={styles.main}>
        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <span className={styles.eyebrow}>
              Open Image &amp; Video Face Swap
            </span>

            <h1>Swap faces in images and videos.</h1>

            <p>
              Upload a source face and a target image or video. Face2Wap
              securely processes your files and generates your result.
            </p>
          </div>

          <UploadClient />
        </section>

        <section id="how-it-works" className={styles.workflow}>
          <div>
            <span>01</span>
            <h2>Upload face</h2>
            <p>Select the source face you want to use.</p>
          </div>

          <div>
            <span>02</span>
            <h2>Add target</h2>
            <p>Choose the image or video where the face will be swapped.</p>
          </div>

          <div>
            <span>03</span>
            <h2>Get result</h2>
            <p>Process the job and download the generated result.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
