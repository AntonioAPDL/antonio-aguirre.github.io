---
layout: default
title: Contact
---

<div class="contact-section">
  <!-- Title -->
  <h1 class="contact-title">Get in Touch</h1>
  
  <!-- Introduction -->
  <p class="contact-description">
    I’d love to connect! Reach out via email or find me on these platforms for professional inquiries, collaborations, or just to say hello.
  </p>

  <!-- Contact Links -->
  <div class="contact-links">
    <ul class="contact-list">
      <li>
        <a href="{{ site.social_media.github }}" target="_blank">
          <i class="fab fa-github"></i>
          <span>GitHub</span>
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.linkedin }}" target="_blank">
          <i class="fab fa-linkedin"></i>
          <span>LinkedIn</span>
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.twitter }}" target="_blank">
          <i class="fab fa-twitter"></i>
          <span>Twitter</span>
        </a>
      </li>
      <li>
        <a href="https://{{ site.social_media.bsky }}" target="_blank">
          <i class="fas fa-circle"></i>
          <span>Bluesky</span>
        </a>
      </li>
      <li>
        <a href="mailto:{{ site.social_media.email }}">
          <i class="fas fa-envelope"></i>
          <span>Email</span>
        </a>
      </li>
    </ul>
  </div>
</div>

<style>
/* Contact Section Styles */
.contact-section {
  text-align: center;
  margin: 2rem auto;
  max-width: 800px;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Title Styles */
.contact-title {
  font-size: 2.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 1rem;
  border-bottom: 3px solid #007acc;
  display: inline-block;
  padding-bottom: 0.3rem;
}

/* Description Styles */
.contact-description {
  font-size: 1.2rem;
  line-height: 1.8;
  color: #555;
  max-width: 600px;
  margin: 0 auto 2rem;
}

/* Contact Links Styles */
.contact-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
}

.contact-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.contact-list li {
  font-size: 1.2rem;
}

.contact-list a {
  text-decoration: none;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
  background-color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: color 0.3s ease, transform 0.2s ease, background-color 0.3s ease;
}

.contact-list a:hover {
  color: #007acc;
  transform: translateY(-2px);
  background-color: #e6f7ff;
}

.contact-list i {
  font-size: 1.8rem;
  color: #007acc;
  transition: color 0.3s ease;
}

.contact-list i:hover {
  color: #005b99;
}
</style>
