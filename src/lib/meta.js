// Site-level metadata. Fill in the arXiv / code URLs once public.
export const META = {
  title: 'Predicting Alignment Generalization with Value Representations',
  short: 'Value Generalization',
  paperUrl: null,                 // TODO: arXiv abs URL (paper links hidden until set)
  codeUrl: null,                  // TODO: e.g. https://github.com/andyjliu/value-generalization
  authors: [
    { name: 'Andy Liu', aff: [1] },
    { name: 'Mehar Bhatia', aff: [2] },
    { name: 'Karolina Stańczak', aff: [3] },
    { name: 'Mona Diab', aff: [1] },
    { name: 'Vered Shwartz', aff: [4] },
    { name: 'Daniel Fried', aff: [1] },
  ],
  affiliations: ['Carnegie Mellon University', 'Mila', 'ETH Zurich', 'University of British Columbia'],
  bibtex: `@article{liu2026predicting,
  title   = {Predicting Alignment Generalization with Value Representations},
  author  = {Liu, Andy and Bhatia, Mehar and Sta{\\'n}czak, Karolina and Diab, Mona and Shwartz, Vered and Fried, Daniel},
  journal = {arXiv preprint},
  year    = {2026}
}`,
};

export const SECTIONS = [
  { id: 'generalization', label: 'Generalization' },
  { id: 'predictors', label: 'Predictors' },
  { id: 'taxonomy', label: 'Taxonomy' },
  { id: 'multivalue', label: 'Multi-value' },
];
