export default function Home() {
  return (
    <main>
      <nav className="glass-nav">
        <div className="nav-left">
          <img src="/logo.png" alt="Logo" className="logo-anim" />
          <span className="gradient-text">ROCKET SHOP</span>
        </div>
        <div className="nav-right">
          <a href="#" className="nav-link">Models</a>
          <a href="#" className="nav-link">Technology</a>
          <a href="#" className="nav-link">About</a>
          <button className="icon-btn">
            <img src="/cart.png" alt="Cart" />
          </button>
          <button className="icon-btn">
            <img src="/user.png" alt="User" />
          </button>
        </div>
      </nav>

      <section className="hero-container">
        <div className="hero-content">
          <h1 className="hero-title">
            Pioneering the <br /> <span className="gradient-text">Next Frontier</span>
          </h1>
          <p className="hero-desc">
            Discover a fully integrated suite of next-generation orbital vehicles. Start your journey today with our state-of-the-art consumer spaceships.
          </p>
          <div className="btn-group">
            <button className="btn-primary">Order Now</button>
            <button className="btn-secondary">View Specs</button>
          </div>
        </div>
        
        <div className="hero-image-container">
          <div className="glow-orb"></div>
          <img src="/hero.png" alt="Hero Rocket" className="hero-rocket-img" />
        </div>
      </section>
    </main>
  );
}
