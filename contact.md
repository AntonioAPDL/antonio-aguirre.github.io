---
layout: default
title: Contact
---
<div class="contact-section">
  <h1>Contact Me</h1>
  <p>Connect with me on the following platforms:</p>
  <div class="contact-links">
    <ul class="social-links">
      <li>
        <a href="{{ site.social_media.github }}" target="_blank">
          <i class="fab fa-github"></i> GitHub
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.linkedin }}" target="_blank">
          <i class="fab fa-linkedin"></i> LinkedIn
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.twitter }}" target="_blank">
          <i class="fab fa-twitter"></i> Twitter
        </a>
      </li>
      <li>
        <a href="https://{{ site.social_media.bsky }}" target="_blank">
          <img src="/files/images/Bluesky_Social_Logo_Vector.svg" alt="Bluesky" class="social-icon"> Bluesky
        </a>
      </li>
      <li>
        <a href="{{ site.social_media.email }}">
          <i class="fas fa-envelope"></i> Email
        </a>
      </li>
    </ul>
  </div>
</div>


<style>
  .contact-section {
    text-align: center;
    margin: 2rem 0;
  }

  .contact-links {
    display: flex;
    justify-content: center;
  }

  .contact-list {
    list-style: none;
    padding: 0;
    display: flex;
    gap: 2rem;
  }

  .contact-list li {
    font-size: 1.2rem;
  }

  .contact-list a {
    text-decoration: none;
    color: #313131;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .contact-list a:hover {
    color: #007acc;
  }

  .contact-list i {
    font-size: 1.5rem;
  }
</style>
