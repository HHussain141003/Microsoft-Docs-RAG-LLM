const { chromium } = require("playwright");
const sqlite3 = require("sqlite3").verbose();
const { open } = require("sqlite");

class MicrosoftDocsScraper {
  constructor() {
    this.db = null;
    this.pendingDocs = [];
    this.totalProcessed = 0;
    this.totalSkipped = 0;
    this.queue = [];
    this.visitedUrls = new Set();
    this.BATCH_SIZE = 20;
    this.MAX_WORKERS = 4;
    this.browser = null;

    this.ALLOWED_PATTERNS = [
      /^https:\/\/learn\.microsoft\.com\/en-us\/azure\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/dotnet\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/sql\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/microsoft-365\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/graph\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/visualstudio\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/power-platform\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/power-apps\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/power-automate\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/power-bi\//,
      /^https:\/\/learn\.microsoft\.com\/en-us\/power-pages\//,
    ];
  }

  // Helper function to normalize URLs by removing fragments and query params
  normalizeUrl(url) {
    try {
      const urlObj = new URL(url);
      // Remove fragment (#) and common tracking parameters
      urlObj.hash = "";
      urlObj.searchParams.delete("view");
      urlObj.searchParams.delete("tabs");
      urlObj.searchParams.delete("pivots");
      return urlObj.toString();
    } catch {
      return url;
    }
  }

  async init() {
    this.db = await open({
      filename: "microsoft_docs.db",
      driver: sqlite3.Database,
    });

    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        title TEXT,
        content TEXT,
        content_type TEXT DEFAULT 'documentation',
        scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        word_count INTEGER,
        category TEXT,
        subcategory TEXT,
        content_hash TEXT
      );
      
      CREATE INDEX IF NOT EXISTS idx_url ON documents(url);
      CREATE INDEX IF NOT EXISTS idx_category ON documents(category);
      CREATE INDEX IF NOT EXISTS idx_content_hash ON documents(content_hash);
    `);

    const existingUrls = await this.db.all("SELECT url FROM documents");
    // Normalize existing URLs to avoid duplicates
    existingUrls.forEach((row) => {
      this.visitedUrls.add(this.normalizeUrl(row.url));
    });

    const baseUrl = "https://learn.microsoft.com/en-us/docs/";
    const normalizedBaseUrl = this.normalizeUrl(baseUrl);
    if (!this.visitedUrls.has(normalizedBaseUrl)) {
      this.queue.push(normalizedBaseUrl);
    }

    console.log(
      `Database initialized with ${existingUrls.length} existing documents`
    );
    console.log(`Queue initialized with ${this.queue.length} URLs to process`);

    return this.visitedUrls;
  }

  isAllowedUrl(url) {
    // Skip URLs with fragments (# anchors) - they're just table of contents links
    if (url.includes("#")) {
      return false;
    }

    // Skip URLs that are samples, API references, or training modules
    const skipPatterns = [
      /\/samples\//,
      /\/training\//,
      /\/learn\/paths\//,
      /\/learn\/modules\//,
      /\/browse\//,
      /\/search\//,
      /\/api\//,
      /\/rest\//,
      /\.zip$/,
      /\.pdf$/,
      /\/download\//,
      /\/media\//,
      /\/includes\//,
    ];

    if (skipPatterns.some((pattern) => pattern.test(url))) {
      return false;
    }

    return this.ALLOWED_PATTERNS.some((pattern) => pattern.test(url));
  }

  async scrapePage(url, browser) {
    const normalizedUrl = this.normalizeUrl(url);

    if (this.visitedUrls.has(normalizedUrl)) {
      console.log(`Already visited: ${normalizedUrl}`);
      return null;
    }

    this.visitedUrls.add(normalizedUrl);
    console.log(`Scraping: ${normalizedUrl}`);

    const page = await browser.newPage();
    try {
      await page.goto(normalizedUrl, {
        waitUntil: "domcontentloaded",
        timeout: 10000,
      });

      // Use the same selector as your working TypeScript version
      await page.waitForSelector('main[role="main"]', { timeout: 10000 });

      const title = await page.title();
      const content = (await page.textContent('main[role="main"]')) || "";

      if (!content || content.trim().length < 200) {
        console.log(`Skipping ${normalizedUrl}: insufficient content`);
        this.totalSkipped++;
        return null;
      }

      // Extract links and normalize them
      const links = await page.$$eval("a", (anchors) =>
        anchors
          .map((a) => a.href)
          .filter((href) => href.includes("learn.microsoft.com/en-us/"))
      );

      // Add new links to queue with filtering and normalization
      let addedLinks = 0;
      for (const link of links) {
        const normalizedLink = this.normalizeUrl(link);

        // Skip if already visited, in queue, or not allowed
        if (
          this.visitedUrls.has(normalizedLink) ||
          this.queue.includes(normalizedLink) ||
          !this.isAllowedUrl(link) ||
          addedLinks >= 15
        ) {
          continue;
        }

        this.queue.push(normalizedLink);
        addedLinks++;
      }

      if (addedLinks > 0) {
        console.log(`Added ${addedLinks} new links to queue`);
      }

      return {
        url: normalizedUrl,
        title: title
          .replace(" | Microsoft Learn", "")
          .replace(" | Microsoft Docs", "")
          .trim(),
        content: content.trim(),
        contentType: "documentation",
      };
    } catch (error) {
      console.error(`Error scraping ${normalizedUrl}:`, error.message);
      this.totalSkipped++;
      return null;
    } finally {
      await page.close();
    }
  }

  async saveDocument(doc) {
    const crypto = require("crypto");
    const contentHash = crypto
      .createHash("md5")
      .update(doc.content)
      .digest("hex");
    const wordCount = doc.content.split(/\s+/).length;

    const urlParts = new URL(doc.url).pathname.split("/").filter((p) => p);
    const category = urlParts[2] || "general";
    const subcategory = urlParts[3] || "general";

    await this.db.run(
      `INSERT OR REPLACE INTO documents 
       (url, title, content, content_type, word_count, category, subcategory, content_hash)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        doc.url,
        doc.title,
        doc.content,
        doc.contentType,
        wordCount,
        category,
        subcategory,
        contentHash,
      ]
    );
  }

  async flushPendingDocs() {
    if (this.pendingDocs.length === 0) return;

    try {
      await this.db.run("BEGIN TRANSACTION");

      for (const doc of this.pendingDocs) {
        await this.saveDocument(doc);
      }

      await this.db.run("COMMIT");
      console.log(`Saved batch of ${this.pendingDocs.length} documents`);

      this.pendingDocs.length = 0;
    } catch (error) {
      await this.db.run("ROLLBACK");
      console.error("Error saving batch:", error);
    }
  }

  async worker(browser) {
    while (this.queue.length > 0) {
      const url = this.queue.shift();
      if (!url) continue;

      try {
        const doc = await this.scrapePage(url, browser);

        if (doc) {
          this.pendingDocs.push(doc);
          this.totalProcessed++;

          if (this.pendingDocs.length >= this.BATCH_SIZE) {
            await this.flushPendingDocs();
          }
        }

        await new Promise((resolve) => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`Worker error on ${url}:`, error.message);
        this.totalSkipped++;
      }
    }
  }

  async processQueue() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      });
    }

    // Progress reporting
    const progressInterval = setInterval(() => {
      console.log(
        `Progress: Processed: ${this.totalProcessed}, Skipped: ${this.totalSkipped}, Queue: ${this.queue.length}`
      );
    }, 30000); // Every 30 seconds

    const workers = [];
    for (let i = 0; i < this.MAX_WORKERS; i++) {
      workers.push(this.worker(this.browser));
    }

    await Promise.all(workers);
    clearInterval(progressInterval);
  }

  async getStats() {
    return await this.db.get(`
      SELECT 
        COUNT(*) as total_docs,
        SUM(word_count) as total_words,
        AVG(word_count) as avg_words_per_doc,
        COUNT(DISTINCT category) as categories,
        MAX(scraped_at) as last_scraped
      FROM documents
    `);
  }

  async exportToFiles() {
    const categories = await this.db.all(
      "SELECT DISTINCT category FROM documents"
    );
    const fs = require("fs-extra");

    await fs.ensureDir("exports");

    for (const { category } of categories) {
      const docs = await this.db.all(
        "SELECT * FROM documents WHERE category = ? ORDER BY subcategory, title",
        [category]
      );

      await fs.writeFile(
        `exports/${category}.json`,
        JSON.stringify(docs, null, 2)
      );

      console.log(`Exported ${docs.length} ${category} documents`);
    }
  }

  async close() {
    await this.flushPendingDocs();

    if (this.browser) {
      await this.browser.close();
    }

    if (this.db) {
      await this.db.close();
    }
  }
}

// Usage
(async () => {
  const scraper = new MicrosoftDocsScraper();

  try {
    await scraper.init();

    console.log("Starting to scrape Microsoft Learn documentation...");
    await scraper.processQueue();

    console.log(
      `Scraping completed! Processed: ${scraper.totalProcessed}, Skipped: ${scraper.totalSkipped}`
    );

    const stats = await scraper.getStats();
    console.log("Final Statistics:", stats);

    if (stats.total_docs > 0) {
      await scraper.exportToFiles();
    }
  } catch (error) {
    console.error("Scraping failed:", error);
  } finally {
    await scraper.close();
  }
})();
