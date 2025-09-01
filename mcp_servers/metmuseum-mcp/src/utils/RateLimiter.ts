class RateLimiter {
  private requestsThisSecond: number = 0;
  private lastRequestTime: number = Date.now();
  private maxRequestsPerSecond: number;

  constructor(maxRequestsPerSecond: number) {
    this.maxRequestsPerSecond = maxRequestsPerSecond;
  }

  async fetch(url: string, options?: RequestInit): Promise<Response> {
    await this.waitIfNeeded();
    return fetch(url, options);
  }

  private async waitIfNeeded(): Promise<void> {
    const now = Date.now();

    // Reset counter if we're in a new second
    if (now - this.lastRequestTime >= 1000) {
      this.requestsThisSecond = 0;
      this.lastRequestTime = now;
    }

    // If we've hit our limit, wait until the next second
    if (this.requestsThisSecond >= this.maxRequestsPerSecond) {
      console.error(`Rate limit of ${this.maxRequestsPerSecond} per second exceeded. Waiting for ${1000 - (now - this.lastRequestTime)}ms`);
      const timeToWait = 1000 - (now - this.lastRequestTime);
      if (timeToWait > 0) {
        await new Promise(resolve => setTimeout(resolve, timeToWait));
      }
      // Reset after waiting
      this.requestsThisSecond = 0;
      this.lastRequestTime = Date.now();
    }

    // Increment counter
    this.requestsThisSecond++;
  }
}

// Create and export a singleton instance for Met Museum API
export const metMuseumRateLimiter = new RateLimiter(80);
