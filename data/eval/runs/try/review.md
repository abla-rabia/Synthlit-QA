# Relecture manuelle

Pour chaque réponse : compte les affirmations (claims_total) et combien sont bien dans les passages cités (claims_supported), puis remplis manual.csv.

Réglages du run : `{"n_extra_queries": 2, "k_per_query": 10, "k_candidates": 10, "k_final": 5, "weight_semantic": 0.7, "weight_keyword": 0.3, "rrf_k": 60, "use_multiquery": true, "use_hybrid": true, "use_rerank": true, "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "query_prefix": "", "history_turns": 4, "llm": "openai/gpt-oss-20b"}`

---

## q01 · specific
**Question :** How many patients were included in the Zimmermann study and what tumour type did they have?
**Référence :** 47 meningioma patients.
**Gold :** 2022_zimmermann_mri-sequence-independent-head-sct-proton | Abstract | p. 1-1 ; 2022_zimmermann_mri-sequence-independent-head-sct-proton | 2.1 Patients | p. 3-3
**Rang du gold :** top10 = 1, top5 = 1

**Réponse du système :**

47 patients, all with meningioma. [1]

**Passages envoyés au LLM :**

- **[1]** Zimmermann et al., 2022 · 2.1 Patient cohort and image acquisition (pp. 2-3) ✔ GOLD (+1 tableau(x))
  > In total 47 meningioma patients treated with proton therapy were included in this study. All patients received MR (Inge-nia 3.0, Philips, Netherlands) and CT (Big Bore CT, Philips, Netherlands) scans on the same day in treatment position using immobilisation devices, like thermoplastic face masks and necessary positioning tools administered during proton irradiation. In more detail the model was trained with data from 33 patients, six patients were used for validation, and eight for testing the model.  All patients were included in a prospective clinical study at the MedAustron Center for Ion Beam Therapy and Research [18], approved by the responsible ethics commit-tee (Niederösterreische Et…
- **[2]** Zimmermann et al., 2022 · 2.1 Patient cohort and image acquisition (p. 3) ✔ GOLD
  > CT images were rigidly registered to all MRIs separately after re-sampling the MRIs to the same voxel dimensions of the pCT. The Elastix implementation in the MICE Toolkit (2020 NONPI Medical AB, Umeå, Sweden) was utilised for the registration.  In the training dataset for all 33 patients, the T1CM-weighted MRI sequence was included, for 24 patients the T1-weighted sequence, and for 32 patients the T2-weighted sequence. For the validation dataset, all six patients received all three sequences. The eight patients representing the test dataset included 16 treatment plans in total. For one of these patients, the T1-weighted sequences, and for three other, the T2-weighted sequence did not fully …
- **[3]** Zimmermann et al., 2022 · 2.2 Clinical treatment plan creation and prescription (p. 3) ✔ GOLD
  > All treatment plans included in this study were clinically approved and delivered, and included three to four beam directions, while the entrance angle differed by at least 20◦. Those plans were recalculated on the sCTs. The relative radiobio-logical effectiveness (RBE)-weighted dose per fraction varied between 1.8 and 2.2 Gy (RBE of protons was assumed with 1.1). Seven of the eight patients received a simultaneous inte-grated boost (SIB) for initial and boost target volume in 27–30 fractions, while one patient received subsequent irradiation of the two target volumes.  The treatment planning system RayStation v8b (Ray- Search, Sweden) employing the Monte Carlo (MC) dose calculation algorith…
- **[4]** Zimmermann et al., 2022 · 4 Discussion (pp. 8-9)
  > The augmentation of training data with different sequences provides the possibility to apply the conversion independently of the sequence used during acqui- sition.  As outlined in Section 2, the total number of T2 images was smaller than the other sequences in the test dataset. In addition, some images were excluded as the T2 sequence did not cover the entire target structure due to the limited FoV of this particular sequence. Further, the performance of the test dataset was inferior to the validation dataset as many patients included had deformations and tumours in the nasal cavity region, which were not present in the training dataset.  Dosimetric comparisons of the recalculated treatment…
- **[5]** Zimmermann et al., 2022 · 4 Discussion (p. 9)
  > The subsequent high impact on the dose volume parameters does not provide additional information on the sCT quality.  Shafai-Erfani et al. [11] investigated patients with base-of-skull tumours for an MRI-only workflow for proton therapy. In their study, the dosimetric evaluation (i.e. Dmean, Dmax, D10%, D50%, and D95%) for the PTV was below 1% and up to 2% for the brain. When comparing our dosimetric results to literature, it has to be stressed, that most comparable studies [6,11] created proton plans on a patient cohort that initially received photon therapy. The only exception being [13], where actual proton treatment plans were applied. Also in the presented study all involved patients re…

---

## q02 · specific
**Question :** Which databases and period did the Dayarathna review search?
**Référence :** Literature search using Scopus and PubMed databases, from 2018 to 2023.
**Gold :** 2024_dayarathna_mri-ct-pet-review | 1. Introduction | p. 2-2
**Rang du gold :** top10 = 2, top5 = 1

**Réponse du système :**

The review searched the Scopus and PubMed databases for articles published from 2018 to July 2023. [1]

**Passages envoyés au LLM :**

- **[1]** Dayarathna et al., 2024 · 1. Introduction (p. 2) ✔ GOLD
  > • This review further identifies challenges and limitations in the current methods and discusses the possible future directions in medical image synthesis.  Search Criteria: We conducted a literature search using Scopus and PubMed databases to find relevant articles published from 2018 to 2023 July with the search term (‘‘synth*’’ OR ‘‘pseudo’’ OR ‘‘translat*’’) AND ‘‘deep learning’’ AND (‘‘medical imag*’’ OR ‘‘CT’’ OR ‘‘MRI’’ OR ‘‘MR’’ OR ‘‘PET’’ OR ‘‘low dose’’ OR ‘‘low count’’ OR ‘‘low field’’) in the title, abstract or keywords. Google Scholar was also used to identify possible omissions and excluded the review articles. We first screened titles and abstracts, considering inclusion crite…
- **[2]** Dayarathna et al., 2024 · 5. Overview of public datasets (p. 19)
  > During image acquisition, one echo was obtained in the almost in-phase (aIP) and another in the almost opposed-phase (aOP). Images were subsequently reconstructed to yield in-phase, opposed-phase, fat-only, and water-only images.  The majority of PET image synthesis studies (Jung et al., 2018; Sikka et al., 2018; Hu et al., 2019; Emami et al., 2020b; Hu et al., 2021; Sikka et al., 2021; Zhang et al., 2022b) relied on the Alzheimer Disease Neuroimaging Initiative (ADNI) database, which provides publicly accessible F18-AV-45 (florbetapir) and F18-FDG (fluorodeoxyglucose) PET images, as well as co-registered T1-weighted MRI data. A few investigations (Rajagopal et al., 2023) utilized private da…
- **[3]** Dayarathna et al., 2024 · 1. Introduction (pp. 2-3) ✔ GOLD
  > Fig. 1. A brief chronology of deep learning networks for medical image synthesis and generation in the literature.  Fig. 2. An overview of the methodological process followed in the literature search flow.  Fig. 3. An overview of the paper organization.
- **[4]** Dayarathna et al., 2024 · 5. Overview of public datasets (p. 19)
  > Studies on medical image synthesis have employed various image modalities and datasets to generate synthesized images. For CT synthesis from MR images, different MR contrasts have been utilized in experiments with paired and unpaired CT images. Most datasets were private and not publicly available except for a few datasets (Oulbacha and Kadoury, 2020; Chen et al., 2021; Ranjan et al., 2022). A summary of publicly available datasets utilized in medical image synthesis is presented in Table 4. T1-weighted and T2-weighted images have been widely used across numerous studies due to their extensive availability and limited training requirements for a single sequence (Hiasa et al., 2018; Lei et al…
- **[5]** Dayarathna et al., 2024 · 6.1. Evaluation based on image related metrics (p. 23)
  > While direct evaluations traditionally focus on the quality of synthesized images, some studies have extended their evaluations to downstream tasks, such as segmentation or classification, to ascertain clinical validity. We overview evaluations concerning synthetic CT, MRI, and PET to underscore their clinical applicability.  Pseudo-CT has been predominantly employed in the context of MRI-only treatment planning. Few studies have evaluated the synthesized CT results to determine their feasibility for treatment planning purposes by focusing primarily on dose distribution estimations and segmentation accuracy rather than relying solely on direct quantitative assessments (Touati et al., 2021; C…

---

## q03 · offtopic
**Question :** What is the capital of Japan?
**Référence :** The system must refuse.
**Gold :** aucun (hors sujet)
**Rang du gold :** top10 = None, top5 = None

**Réponse du système :**

I don't have enough information in the indexed papers to answer this question.

**Passages envoyés au LLM :**

- **[1]** Pepa et al., 2024 · 2.1. Patients Dataset (p. 4)
  > This retrospective study included a consecutive cohort of paediatric (age < 18 years old, yo) and young adult (18 ≤ age ≤ 30) patients treated between December 2021 and December 2023 at the National Centre for Oncological Hadrontherapy (CNAO) in Pavia, Italy. To be eligible for the study, the patients had to meet the following inclusion criteria: (1) age < 30 yo at time of treatment; (2) completion of a full PT course in CNAO; (3) treated for tumours within the pelvic or abdominal district, (4) imaged with in-room CBCT; (4) availability of clinical and imaging data (i.e., pCT and at least one vCT); (5) written informed consent for use of data for clinical research and educational purposes. B…
- **[2]** Liu et al., 2023 · 5. Conclusions (p. 16)
  > All authors have read and agreed to the published version of the manuscript.  Funding: This research was funded by the following grants: (1) the National Key Research and Development Program (No. 2021YFE0202500); (2) Mainland–Hong Kong Joint Funding Scheme (MHKJFS) (MHP/005/20); (3) Health and Medical Research Fund (HMRF 09200576), the Health Bureau, The Government of the Hong Kong Special Administrative Region; (4) Beijing Munici-pal Commission of Science and Technology Collaborative Innovation Project (Z221100003522028); (5) Beijing Natural Science Foundation (Z230003); (6) special fund of the National Clinical Key Specialty Construction Program, P. R. China (2021).  Institutional Review B…
- **[3]** Ramachandran et al., 2026 · 2.1 Study design and patient cohort (p. 3)
  > Imaging acquisition parameters  CT images were acquired on one of two departmental scanners: a Philips® Brilliance™ Big Bore CT or a Toshiba® Aquilion™ Large Bore. Matched acquisition parameters included: 120 kVp, 2 mm slice thickness, 700 mm extended reconstruction field-of-view (FOV), with in-plane pixel spacing of 1.367 × 1.367 mm and matrix size of 512 × 512.Reconstruction was performed using each vendor’s default soft-tissue convolution kernel (Philips®: kernel B; Toshiba®: FC13). Each patient underwent a pCT scan followed by MRI within our radiotherapy department using a 3-Tesla Siemens® MAGNETOM® Vida MR simulator. Axial 3D Gadolinium (Gadovist® 1.0)-enhanced, T1‑weighted Dixon gtMRI …
- **[4]** Yoo et al., 2022 · 5. Conclusions (p. 10)
  > All authors have read and agreed to the published version of the manuscript.  Funding: This work was supported by a National Research Foundation of Korea Grant funded by the Korean government (NRF-2021R1A2C2005824), and a Faculty Research Grant of Yonsei University of College of Medicine (6-2020-0125).  Institutional Review Board Statement: The study was conducted according to the guidelines of the Declaration of Helsinki and approved by the Institutional Review Board of the Severance Hospital (IRB #4-2022-0368).  Informed Consent Statement: The informed consent form was waived due to the retrospective nature of the study.
- **[5]** Ramachandran et al., 2026 · 2.6 Ablation study (pp. 6-7)
  > Contour-based evaluation  To evaluate the clinical utility of the sMRI, contour-based analysis was performed on all ten test-cases using two GTV sub-volumes:the primary GTV at 70 Gy (GTVp_70) and the nodal GTV at 70 Gy (GTVn_70). The gtMRI contours were retrieved from radiotherapy treatment planning DICOM RTSTRUCT files generated by the treating ROs, with consensus as per our departmental guidelines. Before RO review, the gtMRI and the generated sMRI volumes were rescaled from the normalized [0, 1] intensity range to the [0, 255] dis-play range. No histogram matching was applied to the sMRI volumes shown to the ROs. Two evaluating ROs (RO1 and RO2) independently contoured all 10 test-cases o…

---

## q04 · comparaison
**Question :** What are different body regions for medical image synthesis?
**Référence :** pelvis, abdomen, head and neck, brain, thorax, breast, spine, lung
**Gold :** 2024_dayarathna_mri-ct-pet-review | 3.1.1. Model design based on input domain | p. 6-6 ; 2024_dayarathna_mri-ct-pet-review | 6.1. Evaluation based on image related metrics | p. 21-21 ; 2021_rossi_cbct-sct-supervised-vs-unsupervised | 4.3. Technical Challenges and Work Limitations | p. 12-13 ; 2025_guo_ct-synthesis-radiotherapy-review | 5.1. CBCT-Based Online Adaptive Radiotherapy | p. 10-10 ; 2024_sherwani_synthetic-image-radiotherapy-review | 4 Discussion | p. 19-19 ; 2024_sherwani_synthetic-image-radiotherapy-review | 4 Discussion | p. 19-19 ; 2025_molina-maza_cbct-mri-sct-proton-head | 2 STATE-OF-THE-ART | p. 3-3 ; 2023_suwanraksa_cbct-ct-registration-gan-head-neck | 1.3. CT Synthesis Using Deep Learning | p. 3-4 ; 2023_szmul_cbct-sct-abdominal-paediatric | 4.Discussion | p. 15-15
**Rang du gold :** top10 = None, top5 = None

**Réponse du système :**

The reviewed studies focus on two main anatomical regions for medical image synthesis: the human brain and whole‑body scans. [2]

**Passages envoyés au LLM :**

- **[1]** Dayarathna et al., 2024 · Abstract (p. 1)
  > Medical image synthesis represents a critical area of research in clinical decision-making, aiming to overcome the challenges associated with acquiring multiple image modalities for an accurate clinical workflow. This approach proves beneficial in estimating an image of a desired modality from a given source modality among the most common medical imaging contrasts, such as Computed Tomography (CT), Magnetic Resonance Imaging (MRI), and Positron Emission Tomography (PET). However, translating between two image modalities presents difficulties due to the complex and non-linear domain mappings. Deep learning-based generative modelling has exhibited superior performance in synthetic image contra…
- **[2]** Dayarathna et al., 2024 · 5. Overview of public datasets (pp. 19-20)
  > The incorporation of MRI or CT enhanced anatomical details within the synthesized images, which might be overlooked if only LD images were used.  The primary focus region was the human brain, while other studies (Lei et al., 2019a; Häggström et al., 2019;  ×  ✓  PET  Whole-body  Dose PET  FDG-PET/CT Gatidis et al. (2022)  Oncologic FDG-PET/CT  Xue et al., 2021) examined whole-body scans. These investigations included image and projection space input modalities compared to image translation between other modalities. Most input data were in image space, and a few studies employed projection-based sinogram data for FD image synthesis. Most studies utilized private datasets for model training in…
- **[3]** Dayarathna et al., 2024 · 8. Conclusion (p. 27)
  > This review comprehensively examines the recent literature on medical image synthesis. We have assessed various medical image synthesis techniques based on deep learning approaches for pseudo-CT, MR, and PET synthesis. The analysis commences with an overview of the most commonly employed deep learning-based networks in medical image synthesis and synthetic image contrasts. The review’s core analysis emphasizes diverse deep learning approaches based on input domains and network architectures. We further analyse the network models including the most recent generative architectures from the literature and their loss functions, dataset overviews, and evaluation results. Furthermore, we have iden…
- **[4]** Dayarathna et al., 2024 · 1. Introduction (pp. 1-2)
  > Medical imaging is crucial in clinical diagnosis and treatment moni-toring as it provides specific information about the human body. Imaging modalities, including Magnetic Resonance Imaging (MRI), Computed Tomography (CT), and Positron Emission Tomography (PET), are commonly used in clinical workflow, each providing unique structural, functional, and metabolic information that supports comprehensive clinical decisions. However, specific imaging modalities, such as PET and CT, pose a risk of radiation exposure, particularly for paediatric patients (Armanious et al., 2020). Furthermore, the acquisition process of comprehensive multi-modal images is costly, and longer scanner time also introduc…
- **[5]** Dayarathna et al., 2024 · 1. Introduction (p. 2)
  > • This review further identifies challenges and limitations in the current methods and discusses the possible future directions in medical image synthesis.  Search Criteria: We conducted a literature search using Scopus and PubMed databases to find relevant articles published from 2018 to 2023 July with the search term (‘‘synth*’’ OR ‘‘pseudo’’ OR ‘‘translat*’’) AND ‘‘deep learning’’ AND (‘‘medical imag*’’ OR ‘‘CT’’ OR ‘‘MRI’’ OR ‘‘MR’’ OR ‘‘PET’’ OR ‘‘low dose’’ OR ‘‘low count’’ OR ‘‘low field’’) in the title, abstract or keywords. Google Scholar was also used to identify possible omissions and excluded the review articles. We first screened titles and abstracts, considering inclusion crite…

---

## q05 · comparaison
**Question :** What are different Learning paradigms used for medical image synthesis?
**Référence :** Supervised, unsupervised, semi-supervised
**Gold :** 2025_guo_ct-synthesis-radiotherapy-review | 3.5. Hybrid Models | p. 6-7 ; 2025_guo_ct-synthesis-radiotherapy-review | 4. Training Strategies | p. 7-7 ; 2025_guo_ct-synthesis-radiotherapy-review | 4.3. Learning Paradigms | p. 9-9 ; 2021_rossi_cbct-sct-supervised-vs-unsupervised | 1.1. Background | p. 2-2
**Rang du gold :** top10 = None, top5 = None

**Réponse du système :**

The survey identifies two main learning paradigms for medical‑image synthesis:

1. **Supervised learning** – models trained on paired source‑target images to learn a direct mapping between modalities.  
2. **Unsupervised learning** – models that learn from unpaired data, such as CycleGANs, which rely on cycle‑consistency constraints to translate between domains.  

Both paradigms are further enhanced by incorporating attention mechanisms, transformer‑based architectures, diffusion models, and implicit neural representations, but the core learning strategies remain supervised and unsupervised. [5]

**Passages envoyés au LLM :**

- **[1]** Dayarathna et al., 2024 · 8. Conclusion (p. 27)
  > This review comprehensively examines the recent literature on medical image synthesis. We have assessed various medical image synthesis techniques based on deep learning approaches for pseudo-CT, MR, and PET synthesis. The analysis commences with an overview of the most commonly employed deep learning-based networks in medical image synthesis and synthetic image contrasts. The review’s core analysis emphasizes diverse deep learning approaches based on input domains and network architectures. We further analyse the network models including the most recent generative architectures from the literature and their loss functions, dataset overviews, and evaluation results. Furthermore, we have iden…
- **[2]** Dayarathna et al., 2024 · Abstract (p. 1)
  > Medical image synthesis represents a critical area of research in clinical decision-making, aiming to overcome the challenges associated with acquiring multiple image modalities for an accurate clinical workflow. This approach proves beneficial in estimating an image of a desired modality from a given source modality among the most common medical imaging contrasts, such as Computed Tomography (CT), Magnetic Resonance Imaging (MRI), and Positron Emission Tomography (PET). However, translating between two image modalities presents difficulties due to the complex and non-linear domain mappings. Deep learning-based generative modelling has exhibited superior performance in synthetic image contra…
- **[3]** Dayarathna et al., 2024 · 1. Introduction (p. 2)
  > and their reliability and generalizability are limited (Bahrami et al., 2020).  Recently, deep learning has become a prominent approach in computer vision by showing significantly improved performance in medical image synthesis for learning the complex non-linear relationship between image modalities (Wang et al., 2021). This has proven that deep learning-based data-driven methods can accurately model domain-specific characteristics across imaging modalities and synthesize images from different modalities. Further, these deep learning-based methods involve leveraging knowledge adopted from one specific task to improve the performance of another related task with minimal modifi-cation (Spadea…
- **[4]** Wang et al., 2021 · 5 | SUMMARY AND OUTLOOK (p. 20)
  > Recent years have witnessed the trend in deep learning being increasingly used in the application of medical imaging. The latest networks and techniques have been borrowed from the field of computer vision and adapted to specific clinical tasks in radiology and radiation oncology. As reviewed in this paper, learning‐based image synthesis is an emerging and active field — all the reviewed studies were published within the last 3 yr. With further development in both artificial intelligence and computing hardware, more learning‐based methods are expected to facilitate the clinical workflow with novel applications. Although the reviewed literature show the success of deep learning‐based image sy…
- **[5]** Dayarathna et al., 2024 · 7.5. Future directions (p. 26)
  > Potential future research directions in the examined literature can be classified into various aspects, including deep learning networks, datasets, and result validation. Based on the analysis of deep learning-based approaches for medical image translation, most studies concentrate on CT synthesis. Consequently, there is an opportunity for further research on image contrast synthesis using diverse strategies. Additionally, many studies have focused on supervised-based methods to achieve more accurate image synthesis using paired data. While supervised techniques have demonstrated significant results in the image translation process, unsupervised-based methods still possess room for improveme…

---

## q06 · comparaison
**Question :** What is the most commonly used open source dataset for medical image synthesis?
**Référence :** BraTS dataset
**Gold :** 2024_dayarathna_mri-ct-pet-review | 3.3. Synthetic PET | p. 12-12 ; 2022_osman_brain-mri-intramodality-synthesis | 1 Department of Medical Physics,Al-Neelain University,Khartoum 11121,Sudan | p. 1-1 ; 2022_osman_brain-mri-intramodality-synthesis | 2.1 Imaging dataset | p. 3-3 ; 2022_osman_brain-mri-intramodality-synthesis | 2.2 Preprocessing | p. 3-3 ; 2022_osman_brain-mri-intramodality-synthesis | 3.2 Model performance | p. 7-7 ; 2022_osman_brain-mri-intramodality-synthesis | 4 DISCUSSION | p. 8-8
**Rang du gold :** top10 = None, top5 = None

**Réponse du système :**

I don't have enough information in the indexed papers to answer this question.

**Passages envoyés au LLM :**

- **[1]** Dayarathna et al., 2024 · 5. Overview of public datasets (p. 19)
  > Studies on medical image synthesis have employed various image modalities and datasets to generate synthesized images. For CT synthesis from MR images, different MR contrasts have been utilized in experiments with paired and unpaired CT images. Most datasets were private and not publicly available except for a few datasets (Oulbacha and Kadoury, 2020; Chen et al., 2021; Ranjan et al., 2022). A summary of publicly available datasets utilized in medical image synthesis is presented in Table 4. T1-weighted and T2-weighted images have been widely used across numerous studies due to their extensive availability and limited training requirements for a single sequence (Hiasa et al., 2018; Lei et al…
- **[2]** Dayarathna et al., 2024 · Abstract (p. 1)
  > Medical image synthesis represents a critical area of research in clinical decision-making, aiming to overcome the challenges associated with acquiring multiple image modalities for an accurate clinical workflow. This approach proves beneficial in estimating an image of a desired modality from a given source modality among the most common medical imaging contrasts, such as Computed Tomography (CT), Magnetic Resonance Imaging (MRI), and Positron Emission Tomography (PET). However, translating between two image modalities presents difficulties due to the complex and non-linear domain mappings. Deep learning-based generative modelling has exhibited superior performance in synthetic image contra…
- **[3]** Dayarathna et al., 2024 · 8. Conclusion (p. 27)
  > This review comprehensively examines the recent literature on medical image synthesis. We have assessed various medical image synthesis techniques based on deep learning approaches for pseudo-CT, MR, and PET synthesis. The analysis commences with an overview of the most commonly employed deep learning-based networks in medical image synthesis and synthetic image contrasts. The review’s core analysis emphasizes diverse deep learning approaches based on input domains and network architectures. We further analyse the network models including the most recent generative architectures from the literature and their loss functions, dataset overviews, and evaluation results. Furthermore, we have iden…
- **[4]** Wang et al., 2021 · 5 | SUMMARY AND OUTLOOK (p. 21)
  > learning‐based methods require  Unlike conventional methods, large training datasets. The size of training sets has been shown to affect the performance of machine learning in many challenging computer vision problems as well as medical imaging tasks.134–137 Generally, a larger training set size with greater data variation can reduce overfitting of the model and enable better performance. Compared with studies in some medical imaging applications where it is common to see thousands of patients enrolled, studies in medical image synthesis involve far fewer patients. As shown in Tables 1–10, a training size of dozens of patients is more common in these studies while hundreds of patients per se…
- **[5]** Sherwani et al., 2024 · 5.1.3 Datasets, open-source libraries and tools (p. 21)
  > Computer vision techniques are evaluated using a variety of datasets and standards in different branches, including medical imaging (healthcare), agriculture, surveillance, sports and automotive etc. The implementation of DL in computer vision (medical imaging) is limited by a relatively small training dataset and a huge imaging volume. Example datasets include CT medical images (CT images from cancer imaging archive with contrast and patient age), Deep Lesion (contains 32,120 axial CT slices from 10,594 CT scans of 4,427 unique patients), OASIS Brain (Open Access Series of Imaging Studies dataset for normal aging and Alzheimer’s Disease), MRNet (dataset consists of 1,370 knee MRI) and IVDM3…
