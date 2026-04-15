import Image from "next/image";
import styles from "./page.module.css";

export const metadata = {
  title: "Antigravity - AI Pair Programming",
  description: "Advanced agentic coding assistant powered by Google Deepmind technology.",
};

export default function Home() {
  return (
    <div className={styles.main}>
      <div className={styles.backgroundEffects}>
        <div className={styles.blob1}></div>
        <div className={styles.blob2}></div>
      </div>

      <header className={styles.hero}>
        <div className={styles.badge}>
          <span className={styles.badgeHighlight}>New</span> Powered by Google Deepmind Technology
        </div>
        
        <h1 className={styles.title}>
          Meet <span className="text-gradient">Antigravity</span>
        </h1>
        
        <p className={styles.subtitle}>
          The advanced agentic coding assistant that writes the code of the future, today. Seamlessly pair program, build stunning web apps, and eliminate manual drudgery.
        </p>

        <div className={styles.ctaButtons}>
          <button className={styles.primaryAction}>Start Building Free</button>
          <button className={styles.secondaryAction}>Read Documentation</button>
        </div>
      </header>

      <section className={styles.features}>
        <div className={`glass-panel`}>
          <Image 
            src="/brain.png" 
            alt="AI Brain Icon" 
            width={64} 
            height={64} 
            className={styles.featureImage} 
          />
          <h3 className={styles.featureTitle}>Autonomous AI</h3>
          <p className={styles.featureDesc}>
            Powered by advanced models that understand complex codebases, plan architectural implementations, and proactively seek user feedback when needed.
          </p>
        </div>

        <div className={`glass-panel`}>
          <Image 
            src="/code.png" 
            alt="Code Editor Icon" 
            width={64} 
            height={64} 
            className={styles.featureImage} 
          />
          <h3 className={styles.featureTitle}>Deep Tools Integration</h3>
          <p className={styles.featureDesc}>
            Effortlessly interact with your file system, execute arbitrary terminal commands safely, and browse the web using the system browser subagent.
          </p>
        </div>

        <div className={`glass-panel`}>
          <Image 
            src="/rocket.png" 
            alt="Rocket Icon" 
            width={64} 
            height={64} 
            className={styles.featureImage} 
          />
          <h3 className={styles.featureTitle}>Rich App Generation</h3>
          <p className={styles.featureDesc}>
            Rapidly build stunning, dynamic, and state-of-the-art visual web interfaces using Next.js and pure CSS. You dream it, Antigravity builds it.
          </p>
        </div>
      </section>

      <footer className={styles.footer}>
        <p>
          &copy; {new Date().getFullYear()} Antigravity. Designed with <span>♥</span> by Google Deepmind.
        </p>
      </footer>
    </div>
  );
}
