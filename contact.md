---
layout: default
title: Contact
---

<div class="contact-section">
  <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Get in Touch</h1>
  <p style="font-size: 1.2rem; color: #555; max-width: 600px; margin: 0 auto 2rem;">
    I’d love to connect! Reach out via email or find me on these platforms for professional inquiries, collaborations, or just to say hello.
  </p>

  <div class="contact-links">
    <ul class="contact-list">
      <li>
        <a href="{{ site.social_media.github }}" target="_blank">
          <i class="fab fa-github"></i> <span>GitHub</span>
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.linkedin }}" target="_blank">
          <i class="fab fa-linkedin"></i> <span>LinkedIn</span>
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.twitter }}" target="_blank">
          <i class="fab fa-twitter"></i> <span>Twitter</span>
        </a>
      </li>
      <li>
        <a href="https://{{ site.social_media.bsky }}" target="_blank">
          <i class="fab fa-bsky"></i> <span>Bluesky</span>
        </a>
      </li>
      <li>
        <a href="mailto:{{ site.social_media.email }}">
          <i class="fas fa-envelope"></i> <span>Email</span>
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
}

.contact-links {
  display: flex;
  justify-content: center;
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
  transition: color 0.3s ease, transform 0.2s ease;
}

.contact-list a:hover {
  color: #007acc;
  transform: translateY(-2px);
}

.contact-list i {
  font-size: 1.8rem;
  color: #007acc;
}

.contact-list i:hover {
  color: #005b99;
}
</style>
