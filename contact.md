---
layout: default
title: Contact
---

<div class="contact-section">
  <h1>Contact Me</h1>
  <p>Connect with me on these platforms:</p>
  <ul class="contact-links">
    <li><a href="{{ site.social_media.github }}" target="_blank">GitHub</a></li>
    <li><a href="{{ site.social_media.linkedin }}" target="_blank">LinkedIn</a></li>
    <li><a href="{{ site.social_media.twitter }}" target="_blank">Twitter</a></li>
    <li><a href="https://{{ site.social_media.bsky }}" target="_blank">Bluesky</a></li>
    <li><a href="{{ site.social_media.email }}">Email</a></li>
  </ul>
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
